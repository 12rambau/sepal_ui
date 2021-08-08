from traitlets import Unicode, Any, Dict, List, Bool, Int
from pathlib import Path

import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio as rio

from sepal_ui.model import Model
from sepal_ui.scripts import gee
from sepal_ui.scripts import utils as su
from matplotlib.colors import to_rgba


import ee

ee.Initialize()


class ReclassifyModel(Model):
    """
    Reclassification model to store information about the current reclassification and share them within your app. save all the input and output of the reclassification + the the matrix to move from one to another. It is embeding 2 backends, one based on GEE that will use assets as in/out and another based on python that will use local files as in/out. The model can handle both vector and raster data, the format and name of the output will be determined from the the input format/name. The developer will still have the possiblity to choose where to save the outputs (folder name).

    Attributes:
        band (str|int): the band name or number to use for the reclassification if raster type. Use property name if vector type
        src_local (str): the source file to reclassify (from a local path) only used if :code:`gee=False`
        src_gee: (str): AssetId of the used input asset for reclassification. Only used if :code:`gee=True`
        dst_dir (str): the dir used to store the output
        gee (bool): either to use the gee backend or not
        matrix (dict): the transfer matrix between the input and the output using the following format: {old_value: new_value, ...}
        input_type (bool): the input type, 1 for raster and 0 for vector
        src_class (dict): the source classes using the following columns: {code: (desc, color)}
        dst_class (dict): the destination classes using the following columns: {code: (desc, color)}
        dst_local (str): the output file. default to :code:`dst_dir/f'{src_local.stem}_reclass.{src_local.suffix}``
        dst_gee (str): the output assetId. default to :code:`dst_dir/f'{src_gee.stem}_reclass``
        remaped (int): state var updated each time an input is remapped

    Args:
        gee (bool): either or not to set :code:`gee` to True
        dst_dir (str): the destination forlder for outputs
    """

    # inputs
    # should be unicode but we need to handle when nothing is set (None)
    band = Any(None).tag(sync=True)
    src_local = Any(None).tag(sync=True)
    src_gee = Any(None).tag(sync=True)
    dst_dir = Any(None).tag(sync=True)
    gee = Bool(False).tag(sync=True)

    # data manipulation
    matrix = Dict({}).tag(sync=True)

    # outputs
    input_type = Bool(False).tag(sync=True)  # 1 raster, 0 vector
    src_class = Dict({}).tag(sync=True)
    dst_class = Dict({}).tag(sync=True)
    dst_local = Any(None).tag(sync=True)
    dst_gee = Any(None).tag(sync=True)

    # Create a state var, to determine if an asset has been remaped
    remaped = Int(False).tag(sync=True)

    def __init__(self, gee=False, dst_dir=None, **kwargs):

        # init the model
        super().__init__(**kwargs)

        # save the folder where the results should be stored
        # only used for local export
        self.dst_dir = str(Path(dst_dir) if dst_dir else Path.home())

        # save relation with gee
        self.gee = gee

    def save_matrix(self, filename):
        """
        Save the matrix i a csv file

        Return:
            self
        """

        if not len(self.matrix):
            return self

        df = pd.Dataframe(
            {
                "src": [c for c in self.matrix.keys()],
                "dst": [c for c in self.matrix.values()],
            }
        )
        df.to_csv(filename)

        return self

    @staticmethod
    def get_classes(file):
        """
        Extract the classes from the class file. The class file need to be compatible with the reclassify tool i.e. a table file with 3 headerless columns using the following format: 'code', 'desc', 'color'. Color need to be set in hexadecimal to be read else black will be used.

        Args:
            file (pathlike object): the pathlib object of the class file

        Return:
            (dict): the dict of the classes using following format {code: (name, color)}
        """

        path = Path(file)
        if not path.is_file():
            raise Exception(f"{file} is not existing")

        df = pd.read_csv(file, header=None)

        # dst_class_file should be set on the model csv output of the custom view
        # 3 column: 1: code, 2: name, 3: color
        df = df.rename(columns={0: "code", 1: "desc", 2: "color"})

        # save the df for reclassify usage
        class_list = {row.code: (row.desc, row.color) for _, row in df.iterrows()}

        # create a dict out of it
        return class_list

    def get_type(self):
        """
        Guess the type of the input and set the input type attribute for the model (vector or raster)

        Return:
            (bool): the type of input (1 for raster, 0 for vector)
        """

        if self.gee:
            if not self.src_gee:
                raise Exception("Missing gee input")

            asset_info = ee.data.getAsset(self.src_gee)["type"]

            if asset_info == "TABLE":
                self.input_type = False
            elif asset_info == "IMAGE":
                self.input_type = True
            else:
                raise AttributeError(f"Unrecognized asset type: {asset_info}")

        else:
            if not self.src_local:
                raise Exception("no input")

            input_path = Path(self.src_local)

            if input_path.suffix in [".geojson", ".shp"]:
                self.input_type = False
            elif input_path.suffix in [".tif", ".tiff", ".vrt"]:
                self.input_type = True
            else:
                raise AttributeError(f"Unrecognized file format: {input_path.suffix}")

        return self.input_type

    def get_bands(self):
        """
        Use the input_type to extract all the bands/properties from the input

        Return:
            (list): sorted list of all the available bands/properties as integer or str
        """

        @su.need_ee
        def _ee_image(self):

            return sorted(ee.Image(self.src_gee).bandNames().getInfo())

        @su.need_ee
        def _ee_vector(self):

            columns = ee.FeatureCollection(self.src_gee).first().getInfo()["properties"]

            return sorted(
                str(c)
                for c in columns.keys()
                if c not in ["system:index", "Shape_Area"]
            )

        def _local_image(self):

            with rio.open(self.src_local) as f:
                bands = [i for i in range(1, f.count + 1)]

            return sorted(bands)

        def _local_vector(self):

            df = gpd.read_file(self.src_local)

            return [c for c in df.columns.tolist() if c != "geometry"]

        # map all the function in the guess matrix (gee, type)
        band_func = [[_local_vector, _local_image], [_ee_vector, _ee_image]]

        # return the selected function
        # remember to use self as a parameter
        return band_func[self.gee][self.input_type](self)

    def unique(self):
        """
        Retreive all the existing class from the specified band/property according to the input_type.
        The data will be saved in self.src_class with no_name and black as a color.

        Return:
            (Dict): the unique class value found in the specified band/property and there color/name defaulted to none and black
        """

        @su.need_ee
        def _ee_image(self):

            # reduce the image
            image = ee.Image(self.src_gee).select(self.band)
            reduction = image.reduceRegion(
                ee.Reducer.frequencyHistogram(), image.geometry()
            )

            # Remove all the unnecessary reducer output structure and make a list of values.
            values = (
                ee.Dictionary(reduction.get(image.bandNames().get(0))).keys().getInfo()
            )

            return values

        @su.need_ee
        def _ee_vector(self):

            # get the feature
            values = (
                ee.FeatureCollection(self.src_gee).aggregate_array(self.band).getInfo()
            )

            return list(set(values))

        def _local_image(self):

            with rio.open(self.src_local) as src:

                count = np.bincount(src.read(self.band).flatten())

            return np.nonzero(count != 0)[0].tolist()

        def _local_vector(self):

            df = gpd.read_file(self.src_local)

            return df[self.band].unique().tolist()

        # map all the function in the guess matrix (gee, type)
        unique_func = [[_local_vector, _local_image], [_ee_vector, _ee_image]]

        # get values from the selected func
        # remember to use self as a parameter
        values = unique_func[self.gee][self.input_type](self)

        # create the init dictionnary
        self.src_class = {v: ("no_name", "#000000") for v in values}

        return self.src_class

    def reclassify(self):
        """
        Reclassify the input according to the provided matrix. For vector file type reclassifying correspond to add an extra column at the end, for raster the initial class band will be replaced by the new class, the oher being kept unmodified. vizualization colors will be set for both local (QGIS compatible) and assets (SEPAL vizualization compatible).

        Return:
            self
        """

        @su.need_ee
        def _ee_image(self, matrix):

            # create the asset description
            self.dst_gee = Path(self.src_gee).with_name(
                f"{Path(self.src_gee).stem}_reclass"
            )

            # load the image
            # remap according to the matrix
            from_ = [v for v in matrix.keys()]
            to_ = [v for v in matrix.values()]

            ee_image = (
                ee.Image(self.src_gee)
                .remap(from_, to_, 0, self.band)
                .select(["remapped"], [self.band])
            )

            # gather all the other band in the image
            ee_image = ee.Image(self.src_gee).addBands(ee_image, overwrite=True)

            # add colormapping parameters
            # set return an element so we force cast it to ee.Image
            desc = [str(e[0]) for e in self.dst_class.values()]
            color = [str(e[1]) for e in self.dst_class.values()]
            code = [str(e) for e in self.dst_class.keys()]

            ee_image = ee.Image(
                ee_image.set(
                    {
                        "visualization_0_name": "Classification",
                        "visualization_0_bands": self.band,
                        "visualization_0_type": "categorical",
                        "visualization_0_labels": ",".join(desc),
                        "visualization_0_palette": ",".join(color),
                        "visualization_0_values": ",".join(code),
                    }
                )
            )

            # export
            params = {
                "image": ee_image,
                "assetId": str(self.dst_gee),
                "description": self.dst_gee.stem,
                "scale": 30,  # it should be the native resolution of the original image
                "maxPixels": 1e13,
                "pyramidingPolicy": {".default": "mode"},
            }

            task = ee.batch.Export.image.toAsset(**params)
            task.start()

            return

        @su.need_ee
        def _ee_vector(self, matrix):

            # create the asset description
            self.dst_ee = f"{Path(self.src_gee).stem}_reclass"

            # add a new propertie
            def add_prop(feat):
                matrix = ee.Dictionary(matrix)
                new_val = matrix.get(self.feat.get(self.band))
                return ee.Feature(new_val).copyProperties(feat, keepProperties)

            ee_fc = ee.FeatureCollection(self.src_gee).map(add_prop)

            # add colormapping parameters

            # export
            params = {
                "collection": ee_fc,
                "assetId": self.dst_gee,
                "description": self.dst_gee,
            }

            task = ee.batch.Export.table.toAsset(**params)
            task.start()

            return

        def _local_image(self, matrix):

            # set the output file
            self.dst_local = self.dst_dir / f"{Path(self.src_local).stem}_reclass.tif"

            with rio.open(self.src_local) as src_f:

                profile = src_f.profile
                profile.update(driver="GTiff", count=1, compress="lzw", dtype=np.uint8)

                with rio.open(self.dst_local, "w", **profile) as dst_f:

                    # workon each window to avoid memory problems
                    windows = [w for _, w in src_f.block_windows()]
                    for window in windows:

                        # read the window
                        raw = src_f.read(self.band, window=window)

                        # reclassify the image based on the matrix
                        # every value that is not specified will be set to 0
                        data = np.zeros_like(raw, dtype=np.int64)

                        for old_val, new_val in matrix.items():
                            data += (raw == old_val) * new_val

                        # write it in the destination file
                        dst_f.write(data.astype(np.uint8), 1, window=window)

                    # add the colors to the image
                    colormap = {}
                    for code, item in self.dst_class.items():
                        colormap[code] = tuple(int(c * 255) for c in to_rgba(item[1]))

                    dst_f.write_colormap(self.band, colormap)

            return

        def _local_vector(self):

            # set the output file
            self.dst_local = self.dst_dir / f"{Path(self.src_local).stem}_reclass.shp"

            # read the dataset
            gdf = gpd.read_file(self.src_local)

            # map the new column
            gdf["reclass"] = gdf.apply(lambda row: matrix[row[self.band]])

            # add the colors to the gdf
            # waiting for an answer there : https://gis.stackexchange.com/questions/404946/how-can-i-save-my-geopandas-symbology

            # save the file
            gdf.to_file(self.dst_local)

            return

        # map all the function in the guess matrix (gee, type)
        reclassify_func = [[_local_vector, _local_image], [_ee_vector, _ee_image]]

        # reshape the matrix so that every value correspond to 1 key
        matrix = self.matrix

        # return the selected function
        # remember to use self as a parameter
        reclassify_func[self.gee][self.input_type](self, matrix)

        # tel the rest of the apps that a reclassification is finished
        self.remaped += 1

        return self
