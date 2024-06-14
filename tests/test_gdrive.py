import tempfile
from itertools import product
from pathlib import Path

import pytest
import rasterio as rio
from google_drive_downloader import GoogleDriveDownloader as gdd
from googleapiclient.http import MediaFileUpload
from rasterio import windows

from sepal_ui.scripts import gdrive
from sepal_ui.scripts import utils as su


class TestGdrive:
    def test_get_all_items(self, tmp_dem, gdrive_folder):

        # extract name and folder
        tmp_dir, test_file = tmp_dem

        list_items = gdrive.get_all_items()

        # at least the one I added manually
        assert len(list_items) >= 9

        return

    def test_get_items(self, tmp_dem, gdrive_folder):

        # extract name and folder
        tmp_dir, test_file = tmp_dem

        list_items = gdrive.get_items(test_file.stem)

        assert len(list_items) == 9

        return

    def test_download_items(self, tmp_dem, gdrive_folder):

        # extract name and folder
        tmp_dir, test_file = tmp_dem

        # extract all the files from the folder
        with tempfile.TemporaryDirectory() as loc_tmp_dir:

            gdrive.download_items(test_file.stem, loc_tmp_dir)

            loc_tmp_dir = Path(loc_tmp_dir)
            assert len([f for f in loc_tmp_dir.glob("*.tif")]) == 9
            assert len([f for f in loc_tmp_dir.glob("*.vrt")]) == 1

        return

    def test_delete_items(self, tmp_dem, gdrive_folder):

        # extract name and folder
        tmp_dir, test_file = tmp_dem

        gdrive.delete_items(gdrive.get_items(test_file.stem))

        # assert
        assert gdrive.get_items(test_file.stem) == []

        return

    @pytest.fixture(scope="class")
    def gdrive_folder(self, tmp_dem):
        """create a fake folder in my gdrive and run the test over it"""

        # extract name and folder
        tmp_dir, test_file = tmp_dem

        # create a gdrive folder
        body = {
            "name": "test_sepal_ui",
            "mimeType": "application/vnd.google-apps.folder",
        }
        gdrive_folder = gdrive.SERVICE.files().create(body=body).execute()

        # send all the tile files to the gdrive folder
        files = [f for f in tmp_dir.glob("*.tif") if not f.name.endswith("dem.tif")]
        for f in files:
            file_metadata = {"name": f.name, "parents": [gdrive_folder["id"]]}
            media = MediaFileUpload(f, mimetype="image/tiff")
            (
                gdrive.SERVICE.files()
                .create(body=file_metadata, media_body=media)
                .execute()
            )

        yield gdrive_folder

        # delete the folder
        gdrive.SERVICE.files().delete(fileId=gdrive_folder["id"]).execute()

        return

    @pytest.fixture(scope="class")
    def tmp_dem(self):
        """the tmp dir containing the dem"""

        # create a tmp directory and save the DEM file inside
        with tempfile.TemporaryDirectory() as tmp_dir:

            tmp_dir = Path(tmp_dir)

            # save the file
            test_file = tmp_dir / f"{su.random_string(8)}_dem.tif"
            test_id = "1vRkAWQYsLWCi6vcTMk8vLxoXMFbdMFn8"
            gdd.download_file_from_google_drive(test_id, test_file, True, True)

            # cut the image in pieces
            with rio.open(test_file) as src:

                tile_width = int(src.meta["width"] / 2)
                tile_height = int(src.meta["height"] / 2)
                meta = src.meta.copy()

                for window, transform in self.get_tiles(src, tile_width, tile_height):

                    meta["transform"] = transform
                    meta["width"], meta["height"] = window.width, window.height
                    outpath = (
                        tmp_dir
                        / f"{test_file.stem}_{window.col_off}_{window.row_off}.tif"
                    )
                    with rio.open(outpath, "w", **meta) as dst:
                        dst.write(src.read(window=window))

            yield tmp_dir, test_file

        # add this empty line before return to make sure that the file is destroyed
        return

    @staticmethod
    def get_tiles(ds, width, height):
        """
        Cut an image in pieces according to the specified width and height

        Args:
            ds: dataset
            width: the width of the tile
            height; the height of the tile

        Yield:
            (window, transform): the tuple of the window characteristics corresponding to each tile
        """
        ncols, nrows = ds.meta["width"], ds.meta["height"]

        offsets = product(range(0, ncols, width), range(0, nrows, height))
        big_window = windows.Window(col_off=0, row_off=0, width=ncols, height=nrows)
        for col_off, row_off in offsets:
            window = windows.Window(
                col_off=col_off, row_off=row_off, width=width, height=height
            ).intersection(big_window)
            transform = windows.transform(window, ds.transform)
            yield window, transform

        return
