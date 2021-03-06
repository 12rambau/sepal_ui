import unittest

import ipyvuetify as v

from sepal_ui import sepalwidgets as sw

class TestAppBar(unittest.TestCase):
    
    def test_init(self):
        
        #default init
        appBar = sw.AppBar()
        
        self.assertIsInstance(appBar, sw.AppBar)
        self.assertIsInstance(appBar.toggle_button, v.Btn)
        self.assertIsInstance(appBar.children[1], v.ToolbarTitle)
        self.assertEqual(appBar.children[1].children[0], 'SEPAL module')
        
        #exhaustive 
        title = 'toto'
        appBar = sw.AppBar(title)
        self.assertEqual(appBar.children[1].children[0], title)
        
        return
        
    def test_title(self):
        
        appBar = sw.AppBar()
        title = 'toto'
        res = appBar.set_title(title)
        
        self.assertEqual(res, appBar)
        self.assertEqual(appBar.children[1].children[0], title)
        
        return
        
        
if __name__ == '__main__':
    unittest.main()