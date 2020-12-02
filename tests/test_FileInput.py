import unittest
import os

from sepal_ui import sepalwidgets as sw

class TestFileInput(unittest.TestCase):
    
    def test_init(self):
        
        # default init
        file_input = sw.FileInput()

        self.assertIsInstance(file_input, sw.FileInput)
        self.assertEqual(file_input.v_model, '')
        
        # get all the names
        list_names = []
        for list_item in file_input.file_list.children[0].children:
            list_item_content = list_item.children[1]
            list_item_title = list_item_content.children[0]
            list_names.append(list_item_title.children[0])
            
        self.assertIn('sepal_ui', list_names)
        
        # default init
        file_input = sw.FileInput(['.shp'])
        
        return
    
    def test_bind(self):
        
        file_input = sw.FileInput()
        
        class Test_io:
            def __init__(self):
                self.out = None
                
        test_io = Test_io()
        
        output = sw.Alert()
        output.bind(file_input, test_io, 'out')
        
        path = 'toto.ici.shp'
        file_input.v_model = path
        
        self.assertEqual(test_io.out, path)
        self.assertTrue(output.viz)
        
        return
    
    def test_on_file_select(self):
        
        file_input = sw.FileInput()
        
        # move into sepal_ui folders 
        sepal_ui = os.path.join(os.path.expanduser('~'), 'sepal_ui')
        readme = os.path.join(sepal_ui, 'README.md')
        
        file_input._on_file_select({'new' : sepal_ui})
        
        # get all the names
        list_names = []
        for list_item in file_input.file_list.children[0].children:
            list_item_content = list_item.children[1]
            list_item_title = list_item_content.children[0]
            list_names.append(list_item_title.children[0])
        
        self.assertEqual(file_input.v_model, '')
        self.assertIn('README.md', list_names)
        
        # select readme
        file_input._on_file_select({'new': readme})
        self.assertEqual(file_input.v_model, readme)
        
        return
        
        
if __name__ == '__main__':
    unittest.main()