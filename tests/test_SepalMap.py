import unittest
import zipfile
import os
import requests

import ee 
import geemap
from ipyleaflet import basemaps, basemap_to_tiles

from sepal_ui import mapping as sm
from sepal_ui.scripts import utils as su

su.init_ee()

class TestSepalMap(unittest.TestCase):
    
    def test_init(self):

        # check that the map start with no info
        m = sm.SepalMap()
        
        self.assertIsInstance(m, sm.SepalMap)
        self.assertEqual(m.center, [0, 0])
        self.assertEqual(m.zoom, 2)
        self.assertEqual(len(m.layers), 1)
        self.assertEqual(m.layers[0].name, 'CartoDB.DarkMatter')
        
        # check that the map start with a DC 
        m = sm.SepalMap(dc = True)
        self.assertIsInstance(m.dc, geemap.DrawControl)
        
        # check that the map start with several basemaps
        m = sm.SepalMap(['CartoDB.DarkMatter', 'CartoDB.Positron'])
        self.assertEqual(len(m.layers), 2)
        self.assertEqual(m.layers[0].name, 'CartoDB.DarkMatter')
        self.assertEqual(m.layers[1].name, 'CartoDB.Positron')
        
        # check that the map refuses to display basmap if not 
        # part of the leaflet basemap list
        m = sm.SepalMap(['TOTO'])
        self.assertEqual(len(m.layers), 0)
        
        return
    
    def test_set_drawing_controls(self):
        
        m = sm.SepalMap()
        
        # check that the dc is not add on false 
        res = m.set_drawing_controls(False)
        
        self.assertEqual(res, m)
        for control in m.controls:
            self.assertNotEqual(type(control), geemap.DrawControl)
        
        m.set_drawing_controls(True)
        self.assertIsInstance(m.dc, geemap.DrawControl)
        self.assertEqual(m.dc.rectangle, {'shapeOptions': {'color': '#79B1C9'}})
        self.assertEqual(m.dc.polygon, {'shapeOptions': {'color': '#79B1C9'}})
        self.assertEqual(m.dc.marker, {})
        self.assertEqual(m.dc.polyline, {})
        
        return 
    
    def test_remove_local_raster(self):
        # init 
        m = sm.SepalMap()        
        
        # download the raster
        out_dir = os.path.expanduser('~')
        dem = os.path.join(out_dir, 'dem.tif')
        
        if not os.path.exists(dem):
            dem_url = 'https://drive.google.com/file/d/1vRkAWQYsLWCi6vcTMk8vLxoXMFbdMFn8/view?usp=sharing'
            geemap.download_from_gdrive(dem_url, 'dem.tif', out_dir, unzip=False)
        
        # add a raster 
        m.add_raster(dem, colormap='terrain', layer_name='DEM')
        
        # remove it using its name
        res = m.remove_local_raster('DEM')
        
        self.assertEqual(res, m)
        self.assertEqual(len(m.loaded_rasters), 0)
        
        # remove the file 
        os.remove(dem)
        
        return
    
    def test_remove_last_layer(self):
        
        # init 
        m = sm.SepalMap()
        
        # there is just one (the basemap) so not supposed to move
        res = m.remove_last_layer()
        
        self.assertEqual(res, m)
        self.assertEqual(len(m.layers), 1)
        
        # add 1 layer and remove it 
        layer = basemap_to_tiles(basemaps.CartoDB.Positron)
        m.add_layer(layer)
        m.remove_last_layer()
        
        self.assertEqual(len(m.layers), 1)
        
        #######################################################
        ##      TODO problem dealing with local rasters      ##
        #######################################################
        
        # # add 1 local raster
        # out_dir = os.path.expanduser('~')
        # dem = os.path.join(out_dir, 'dem.tif')
        # 
        # if not os.path.exists(dem):
        #     dem_url = 'https://drive.google.com/file/d/1vRkAWQYsLWCi6vcTMk8vLxoXMFbdMFn8/view?usp=sharing'
        #     geemap.download_from_gdrive(dem_url, 'dem.tif', out_dir, unzip=False)
        # 
        # # add a raster 
        # m.add_raster(dem, colormap='terrain', layer_name='DEM')
        # 
        # # remove it 
        # m.remove_last_layer()
        # 
        # self.assertEqual(len(m.layers), 1)
        # self.assertEqual(len(m.loaded_rasters), 0)
        # 
        # # remove the file 
        # os.remove(dem)
        
        return 
    
    def zoom_ee_object(self):
        
        # init objects
        m = sm.SepalMap() 
        ee_object = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', 'France'))
        
        # zoom without zoom out 
        m.zoom_ee_object(ee_object.geometry())
        
        self.assertEqual(m.center, [46.5135930048161, 2.574509802526499])
        self.assertEqual(m.zoom, 5.)
        
        # zoom with a zoom_out option 
        m.zoom_ee_object(ee_object.geometry(), 3)
        
        self.assertEqual(m.zoom, 4)
        
        return 
    
    def test_zoom_bounds(self):
        
        # init objects 
        m = sm.SepalMap()
        bounds = (
            (45.73871293893269, 4.804066607988262), # tl
            (45.73871293893269, 4.9050034976367),   # bl
            (45.7746437385302, 4.9050034976367),    # tr
            (45.7746437385302, 4.804066607988262),  # br
        )
        
        # zoom without zoom_out 
        m.zoom_bounds(bounds)
        self.assertEqual(m.zoom, 14.)
        
        # zoom with zoom_out 
        m.zoom_bounds(bounds, 5)
        self.assertEqual(m.zoom, 10.)
         
        
        return 
    
    def test_update_map(self):
        
        # create a map 
        
        # add a false layer 
        
        # update with a new one 
        
        # check layers 
        
        # check center 
        
        # check zoom level 
        
        # add a new one removing the one before 
        
        # check that the previous one has bee removed 
        
        return 
    
    def test_add_raster(self):
        
        # create a map 
        
        # load a 1 band raster 
        
        # check response when the image doesn't exist 
        
        # check name 
        
        # check the colormap 
        
        # check opacity 
        
        # check that repeated name lead to specific strings 
        
        # load a multiband file 
        
        # check that it's displayed 
        
        # force opacity of the layer 
        
        # test > 1 opacity settings 
        
        return 
    
    def test_show_dc(self):
        
        # add a map with a dc
        m = sm.SepalMap(dc=True)
        
        # draw something 
        
        # show dc 
        res = m.show_dc()
        
        self.assertEqual(res, m)
        # check that dc is clear
        # check that dc is in the control list 
        
        return 
    
    def hide_dc(self):
    
        # add a map with a dc 
        m = sm.SepalMap(dc=True)
        
        # show dc 
        m.show_dc()
        
        # draw something 
        
        # hide it 
        res = m.hide_dc()
        
        self.assertEqual(res, m)
        # check that dc is clear 
        # check that dc is not in the control list anymore
        
        return 
            
if __name__ == '__main__':
    unittest.main()