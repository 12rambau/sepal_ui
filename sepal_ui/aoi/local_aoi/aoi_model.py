import json
from pathlib import Path
from traitlets import Any
from urllib.request import urlretrieve

import pandas as pd
import geopandas as gpd
from ipyleaflet import GeoJSON

from sepal_ui.frontend.styles import AOI_STYLE
from sepal_ui.scripts import utils as su
from sepal_ui.message import ms
from sepal_ui.model import Model


class AoiModel(Model):
    
    # const params
    GADM_FILE = Path(__file__).parents[2]/'scripts'/'gadm_database.csv' # the file location of the database
    GADM_BASE_URL = "https://biogeo.ucdavis.edu/data/gadm3.6/gpkg/gadm36_{}_gpkg.zip" # the base url to download gadm maps

    GADM_ZIP_DIR = Path('~', 'tmp', 'GADM_zip').expanduser() # the zip dir where we download the zips
    GADM_ZIP_DIR.mkdir(parents=True, exist_ok=True)
    
    # widget related traitlets
    
    method = Any(None).tag(sync=True)
    
    default_vector = Any(None).tag(sync=True)
    default_admin = Any(None).tag(syn=True)
    point_json = Any(None).tag(sync=True) # information that will be use to transform the csv into a gdf
    vector_json = Any(None).tag(sync=True) # information that will be use to transform the vector file into a gdf
    geo_json = Any(None).tag(sync=True) # the drawn geojson featureCollection
    admin = Any(None).tag(sync=True)
    
    name = Any(None).tag(sync=True) # the name of the file (use only in drawn shaped)

    def __init__(self, alert, default_vector = None, default_admin=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        # outputs of the selection
        self.gdf = None
        self.ipygeojson = None
        self.selected_feature = None
        
        # the Alert used to display information
        self.alert = alert
        
        # set default values
        self.set_default(default_vector, default_admin)
        
        
    def set_default(self, default_vector=None, default_admin=None):
        """
        Set the default value of the object and create a gdf out of it
        
        Params:
            default_vector (str, pathlib.path): the default vector file that 
                will be used to produce the gdf. need to be readable by fiona and/or GDAL/OGR
            default_admin (str): the default administrative area in GADM norm
            
        Return:
            self
        """
        
        # save the default values
        self.default_vector = default_vector
        
        self.vector_json = {
            'pathname': str(default_vector), 
            'column': None, 
            'value': None
        } if default_vector else None
        
        self.default_admin = self.admin = default_admin
        
        # set the default gdf in possible 
        if self.vector_json != None:
            self.set_gdf('SHAPE')
        elif self.admin != None:
            self.set_gdf('ADMIN0') #any level will work
            
        return self
    
    def get_ipygeojson(self):
        """ 
        Converts current geopandas object into ipyleaflet GeoJSON
        
        Return: 
            (GeoJSON): the geojson layer of the aoi gdf
        """
        
        if type(self.gdf) == type(None):
            raise Exception("You must set the gdf before converting it into GeoJSON")
    
        data = json.loads(self.gdf.to_json())
        self.ipygeojson = GeoJSON(data=data, style=AOI_STYLE, name='aoi')
        
        return self.ipygeojson
    
    def set_gdf(self, method=None):
        """
        set the gdf based on the model inputs. The method can be manually overwrite
        
        Args:
            method (str| optional): a model method
        
        Return:
            self
        """
        
        # overwrite self.method
        self.method = method or self.method
        
        if self.method in ['ADMIN0', 'ADMIN1', 'ADMIN2']:
            self._from_admin(self.admin)
        elif self.method == 'POINTS':
            self._from_points(self.point_json)
        elif self.method == 'SHAPE':
            self._from_vector(self.vector_json)
        elif self.method == 'DRAW':
            self._from_geo_json(self.geo_json)
        else:
            raise Exception(ms.aoi_sel.no_inputs)
            
        self.alert.add_msg(ms.aoi_sel.complete, "success")
        
        return self

    
    def _from_points(self, point_json):
        """set the gdf output from a csv json"""
        
        if not all(point_json.values()):
            raise Exception('All fields are required, please fill them.')
            
        # cast the pathname to pathlib Path
        point_file = Path(point_json['pathname'])
    
        # check that the columns are well set 
        values = [v for v in point_json.values()]
        if not len(values) == len(set(values)):
            raise Exception(ms.aoi_sel.duplicate_key)
    
        # create the gdf
        df = pd.read_csv(point_file, sep=None, engine='python')
        self.gdf = gpd.GeoDataFrame(
            df, 
            crs='EPSG:4326', 
            geometry = gpd.points_from_xy(
                df[point_json['lng_column']], 
                df[point_json['lat_column']])
        )
        
        # set the name
        self.name = point_file.stem
        
        return self
    
    def _from_vector(self, vector_json):
        """set the gdf output from a vector json"""
        
        if not (vector_json['pathname']):
            raise Exception('Please select a file.')
        
        if vector_json['column'] != 'ALL':
            if vector_json['value'] is None:
                raise Exception('Please select a value.')
            
        # cast the pathname to pathlib Path
        vector_file = Path(vector_json['pathname'])
        
        # create the gdf
        self.gdf = gpd.read_file(vector_file).to_crs("EPSG:4326")
        
        # set the name using the file stem
        self.name = vector_file.stem
        
        # filter it if necessary
        if vector_json['value']:
            self.gdf = self.gdf[self.gdf[vector_json['column']] == vector_json['value']]
            self.name = f"{self.name}_{vector_json['column']}_{vector_json['value']}"
        
        return self
    
    def _from_geo_json(self, geo_json):
        """set the gdf output from a geo_json"""
        
        if not geo_json:
            raise Exception('Please draw a shape in the map')
        
        # create the gdf
        self.gdf = gpd.GeoDataFrame.from_features(geo_json)
        
        # normalize the name
        self.name =su.normalize_str(self.name)
        
        # save the geojson in downloads 
        path = Path('~', 'downloads', 'aoi').expanduser()
        path.mkdir(exist_ok=True, parents=True) # if nothing have been run the downloads folder doesn't exist
        self.gdf.to_file(path/f'{self.name}.geojson', driver='GeoJSON')
        
        return self
            
    def _from_admin(self, admin):
        
        """Set the gdf according to given an administrative number in 
        the GADM norm. The gdf will be projected in EPSG:4326"""
        
        if not admin:
            raise Exception('Select an administrative layer')
            
        # save the country iso_code 
        iso_3 = admin[:3]
        
        # get the admin level corresponding to the given admin code
        gadm_df = pd.read_csv(self.GADM_FILE)
        
        # extract the first element that include this administrative code and set the level accordingly 
        is_in = gadm_df.filter(['GID_0', 'GID_1', 'GID_2']).isin([admin])
        
        if not is_in.any().any():
            raise Exception("The code is not in the database")
        else:
            level = is_in[~((~is_in).all(axis=1))].idxmax(1).iloc[0][-1] # last character from 'GID_X' with X being the level
            
        # download the geopackage in tmp 
        zip_file = self.GADM_ZIP_DIR/f'{iso_3}.zip'
        
        if not zip_file.is_file():
            
            # get the zip from GADM server only the ISO_3 code need to be used
            urlretrieve(self.GADM_BASE_URL.format(iso_3), zip_file)
            
        # read the geopackage 
        layer_name = f"gadm36_{iso_3}_{level}"
        level_gdf = gpd.read_file(f'{zip_file}!gadm36_{iso_3}.gpkg', layer=layer_name)
        
        # note that the runtime warning is not display when reading from a ZIP
        
        # get the exact admin from this layer 
        self.gdf = level_gdf[level_gdf[f'GID_{level}'] == admin]
        
        # set the name using the layer 
        r = self.gdf.iloc[0]
        names = [su.normalize_str(r[f'NAME_{i}']) if i else r['GID_0'] for i in range(int(level)+1)]
        self.name = '_'.join(names)
        
        return self
    
    def clear_attributes(self):
        """
        Return all attributes to their default state.
        Set the default setting as current gdf.

        Return: 
            self
        """

        # keep the default 
        default_admin = self.default_admin
        default_vector = self.default_vector 

        # delete all the traits
        [setattr(self, attr, None) for attr in self.trait_names()]
        
        # reset the outputs
        self.gdf = None
        self.ipygeojson = None
        self.selected_feature = None

        # reset the default 
        self.set_default(default_vector, default_admin)

        return self

    def get_columns(self):
        """Return all columns skiping geometry""" 
        
        if type(self.gdf) == type(None):
            raise Exception("You must set the gdf before interacting with it")
        
        return sorted(list(set(['geometry'])^set(self.gdf.columns.to_list())))
        
    def get_fields(self, column):
        """Return fields from selected column."""
        
        if type(self.gdf) == type(None):
            raise Exception("You must set the gdf before interacting with it")
        
        return sorted(self.gdf[column].to_list())
    
    def get_selected(self, column, field):
        """Get selected element"""
        
        if type(self.gdf) == type(None):
            raise Exception("You must set the gdf before interacting with it") 
        
        return self.gdf[self.gdf[column] == field]
        