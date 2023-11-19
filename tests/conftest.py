"""The configuration of the pytest run."""

import json
import os
import uuid
from itertools import product
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional
from urllib.request import urlretrieve

import ee
import geopandas as gpd
import matplotlib
import pandas as pd
import pytest
from shapely import geometry as sg

import sepal_ui.sepalwidgets as sw
from sepal_ui.scripts import gee
from sepal_ui.scripts import utils as su

try:
    su.init_ee()
except Exception:
    pass  # try to init earthengine. use ee.data._credentials to skip

# -- a component to fake the display in Ipython --------------------------------


@pytest.fixture(scope="session")
def _alert() -> sw.Alert:
    """An alert that can be used everywhere to display information.

    Returns:
        an alert object
    """
    return sw.Alert()


@pytest.fixture(scope="function")
def alert(_alert: sw.Alert) -> sw.Alert:
    """An alert that can be used everywhere to display information.

    Args:
        _alert: the shared alert component

    Returns:
        an alert object
    """
    return _alert.reset()


# -- SEPAL related parameters --------------------------------------------------


@pytest.fixture(scope="session")
def file_start() -> str:
    """The start of any link to the sepal platform.

    Args:
        the value of the sandbox path
    """
    return "https://sepal.io/api/sandbox/jupyter/files/"


# -- Access files from the project ---------------------------------------------

# init pyplot with the non interactive backend and use it in the rest of the tests
matplotlib.use("Agg")


@pytest.fixture(scope="session")
def root_dir() -> Path:
    """Path to the root dir of the library.

    Returns:
        the root path
    """
    return Path(__file__).parents[1].absolute()


@pytest.fixture(scope="session")
def readme(root_dir: Path) -> Path:
    """Return the readme file path.

    Returns:
        the path to the file
    """
    return root_dir / "README.rst"


# -- generate a test file system in GEE ----------------------------------------


@pytest.fixture(scope="session")
def _hash() -> str:
    """Create a hash for each test instance.

    Returns:
        the hash string
    """
    return uuid.uuid4().hex


@pytest.fixture(scope="session")
def gee_dir(_hash: str) -> Optional[Path]:
    """Create a test dir based on earthengine initialization.

    Populated with fake super small assets:

    sepal-ui-<hash>/
    ├── subfolder/
    │   └── subfolder_feature_collection
    ├── feature_collection
    └── image

    remove everything on teardown

    Returns:
        the path to the gee dir inside user folder
    """
    if not ee.data._credentials:
        pytest.skip("Eathengine is not connected")

    # create a test folder with a hash name
    root = ee.data.getAssetRoots()[0]["id"]
    gee_dir = Path(root) / f"sepal-ui-{_hash}"
    ee.data.createAsset({"type": "FOLDER"}, str(gee_dir))

    # create a subfolder
    subfolder = gee_dir / "subfolder"
    ee.data.createAsset({"type": "FOLDER"}, str(subfolder))

    # create test material
    centers = [sg.Point(i, j) for i, j in product([-50, 50], repeat=2)]
    data = list(range(len(centers)))
    gdf = gpd.GeoDataFrame({"data": data, "geometry": centers}, crs=3857).to_crs(4326)
    ee_gdf = ee.FeatureCollection(gdf.__geo_interface__)

    image = ee.Image.random().multiply(4).byte()

    lon = ee.Image.pixelLonLat().select("longitude")
    lat = ee.Image.pixelLonLat().select("latitude")
    image = (
        ee.Image(1)
        .where(lon.gt(0).And(lat.gt(0)), 2)
        .where(lon.lte(0).And(lat.lte(0)), 3)
        .where(lon.gt(0).And(lat.lte(0)), 4)
    )
    ee_buffer = ee.Geometry.Point(0, 0).buffer(200).bounds()
    image = image.clipToBoundsAndScale(ee_buffer, scale=30)

    # exports It should take less than 2 minutes unless there are concurrent tasks
    fc = "feature_collection"
    ee.batch.Export.table.toAsset(
        collection=ee_gdf, description=f"{fc}_{_hash}", assetId=str(gee_dir / fc)
    ).start()

    subfolder_fc = "subfolder_feature_collection"
    ee.batch.Export.table.toAsset(
        collection=ee_gdf,
        description=f"{subfolder_fc}_{_hash}",
        assetId=str(subfolder / subfolder_fc),
    ).start()

    rand_image = "image"
    ee.batch.Export.image.toAsset(
        image=image,
        description=f"{rand_image}_{_hash}",
        assetId=str(gee_dir / rand_image),
        region=ee_buffer,
    ).start()

    # wait for completion of the exportation tasks before leaving this method
    # image should be the longest
    gee.wait_for_completion(f"{fc}_{_hash}")
    gee.wait_for_completion(f"{subfolder_fc}_{_hash}")
    gee.wait_for_completion(f"{rand_image}_{_hash}")

    yield gee_dir

    # flush the directory and it's content
    gee.delete_assets(str(gee_dir), False)

    return


@pytest.fixture(scope="session")
def fake_asset(gee_dir: Path) -> Path:
    """Return the path to a fake asset.

    Returns:
        the path to the dir
    """
    return gee_dir / "feature_collection"


@pytest.fixture(scope="session")
def gee_user_dir(gee_dir: Path) -> Path:
    """Return the path to the gee_dir assets without the project elements.

    Args:
        gee_dir: the path to the session defined GEE directory

    Returns:
        the path to gee_dir
    """
    legacy_project = Path("projects/earthengine-legacy/assets")

    return gee_dir.relative_to(legacy_project)


@pytest.fixture(scope="session")
def image_id() -> str:
    """The image id of an asset.

    Returns:
        the AssetId of Daniel Wiell asset
    """
    # testing asset from Daniel Wiell
    # may not live forever
    return "users/wiell/forum/visualization_example"


# -- create local tmp files ----------------------------------------------------


@pytest.fixture(scope="session")
def tmp_dir() -> Path:
    """Creates a temporary local directory to store data.

    Returns:
        path to to tmp created directory
    """
    with TemporaryDirectory() as tmp_dir:

        yield Path(tmp_dir)

    return


@pytest.fixture(scope="session")
def fake_vector() -> Path:
    """Create a fake vector file from the GADM definition of vatican city and save it in the tmp dir.

    Returns:
        the path to the tmp vector file
    """
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        link = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_VAT_0.json"
        file = tmp_dir / "gadm41_VAT_0.shp"
        gpd.read_file(link).to_file(file)

        yield file

    return


@pytest.fixture(scope="session")
def fake_points() -> Path:
    """Create a fake point file the tmp file.

    Returns:
        the path to the point file
    """
    with NamedTemporaryFile(suffix=".csv") as tmp_file:
        tmp_file = Path(tmp_file.name)
        data = "lat,lon,id\n1,1,0\n0,0,1"
        tmp_file.write_text(data)

        yield tmp_file

    return


@pytest.fixture(scope="session")
def fake_table() -> Path:
    """Create a fake table.

    Returns:
        the path to the created file
    """
    with NamedTemporaryFile(suffix=".csv") as tmp_file:
        tmp_file = Path(tmp_file.name)

        coloseo = [1, 41.89042582290999, 12.492241627092199]
        fao = [2, 41.88369224629387, 12.489216069409004]
        columns = ["id", "lat", "lng"]
        df = pd.DataFrame([coloseo, fao], columns=columns)

        df.to_csv(tmp_file, index=False)

        yield tmp_file

    return


@pytest.fixture(scope="session")
def wrong_table(fake_table: Path) -> Path:
    """Create a wrongly defined table (with 2 columns instead of the minimal 3.

    Args:
        fake_table: the path to the complete table

    Returns:
        the Path to the created file
    """
    with NamedTemporaryFile(suffix=".csv") as tmp_file:
        tmp_file = Path(tmp_file.name)
        df = pd.read_csv(fake_table).drop(["lng"], axis=1)
        df.to_csv(tmp_file, index=False)

        yield tmp_file

    return


@pytest.fixture(scope="session")
def rgb() -> Path:
    """Add a raster file of the bahamas coming from rasterio test suit.

    Returns:
        the path to the image
    """
    with NamedTemporaryFile(suffix=".tif") as file:
        file = Path(file.name)
        link = "https://raw.githubusercontent.com/rasterio/rasterio/master/tests/data/RGB.byte.tif"
        urlretrieve(link, file)

        yield file

    return


@pytest.fixture(scope="session")
def byte() -> Path:
    """Add a raster file of the bahamas coming from rasterio test suit.

    Returns:
        the path to the byte file
    """
    with NamedTemporaryFile(suffix=".tif") as file:
        file = Path(file.name)
        link = "https://raw.githubusercontent.com/rasterio/rasterio/master/tests/data/byte.tif"
        urlretrieve(link, file)

        yield file

    return


# -- Planet credentials --------------------------------------------------------


@pytest.fixture(scope="session")
def planet_key() -> str:
    """Get the planet key stored in env.

    Returns:
        the str key
    """
    return os.getenv("PLANET_API_KEY")


@pytest.fixture(scope="session")
def cred() -> list:
    """Get the credentials stored in env.

    Returns:
        credential as a list: [cred(username, password)]
    """
    credentials = json.loads(os.getenv("PLANET_API_CREDENTIALS"))

    return list(credentials.values())


@pytest.fixture(scope="session")
def repo_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a dummy repo directory.

    Returns:
        Path to the repo dir
    """
    return tmp_path_factory.mktemp("repo_dir")
