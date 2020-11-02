####################################
##      init ee with service      ##
####################################
import ee
import os 

#service_account = 'sepal-ui@aesthetic-site-125712.iam.gserviceaccount.com'
#credentials = ee.ServiceAccountCredentials(service_account, 'keys.json')
#ee.Initialize(credentials) 
####################################

import unittest

import ipyvuetify as v

from sepal_ui import aoi as sw

@unittest.skip('impossible to automatically test EE API')
class TestAoiTile(unittest.TestCase):

    def test_init(self):
        
        ###################################################
        ##      impossible to automatically test EE      ##
        ###################################################
        
        aoi_io = sw.Aoi_io()
        
        #default init
        tile = sw.TileAoi(aoi_io)
        
        self.assertIsInstance(tile, sw.TileAoi)        
        
        return
        
if __name__ == '__main__':
    unittest.main()