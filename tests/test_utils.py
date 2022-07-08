import random
import warnings
from configparser import ConfigParser
from unittest.mock import patch

import ee
import geopandas as gpd
import ipyvuetify as v
import pytest
from shapely import geometry as sg

from sepal_ui import config_file
from sepal_ui import sepalwidgets as sw
from sepal_ui.frontend.styles import TYPES
from sepal_ui.scripts import utils as su
from sepal_ui.scripts.warning import SepalWarning


class TestUtils:
    def test_hide_component(self):

        # hide a normal v component
        widget = v.Btn()
        su.hide_component(widget)
        assert "d-none" in widget.class_

        # hide a sepalwidget
        widget = sw.Btn()
        su.hide_component(widget)
        assert widget.viz is False

        return

    def test_show_component(self):

        # show a normal v component
        widget = v.Btn()
        su.hide_component(widget)
        su.show_component(widget)
        assert "d-none" not in widget.class_

        # show a sepalwidget
        widget = sw.Btn()
        su.hide_component(widget)
        su.show_component(widget)
        assert widget.viz is True

        return

    def test_download_link(self):

        # check the URL for a 'toto/tutu.png' path
        path = "toto/tutu.png"

        expected_link = "https://sepal.io/api/sandbox/jupyter/files/"

        res = su.create_download_link(path)

        assert expected_link in res

        return

    def test_random_string(self):

        # use a seed for the random function
        random.seed(1)

        # check default length
        str_ = su.random_string()
        assert len(str_) == 3
        assert str_ == "esz"

        # check parameter length
        str_ = su.random_string(6)
        assert len(str_) == 6
        assert str_ == "ycidpy"

        return

    def test_get_file_size(self):

        # init test values
        test_value = 7.5
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

        # mock 0 B file
        with patch("pathlib.Path.stat") as stat:
            stat.return_value.st_size = 0

            txt = su.get_file_size("random")
            assert txt == "0B"

        # mock every pow of 1024 to YB
        for i in range(9):
            with patch("pathlib.Path.stat") as stat:
                stat.return_value.st_size = test_value * (1024**i)

                txt = su.get_file_size("random")
                assert txt == f"7.5 {size_name[i]}"

        return

    def test_init_ee(self):

        # check that no error is raised
        su.init_ee()

        return

    def test_catch_errors(self):

        # create a fake object that uses the decorator
        class Obj:
            def __init__(self):
                self.alert = sw.Alert()
                self.btn = sw.Btn()

                self.func1 = su.catch_errors(alert=self.alert)(self.func)
                self.func2 = su.catch_errors(alert=self.alert, debug=True)(self.func)

            def func(self, *args):
                return 1 / 0

        obj = Obj()

        obj.func1()
        assert obj.alert.type == "error"
        with pytest.raises(Exception):
            obj.func2()

        return

    def test_loading_button(self):

        # create a fake object that uses the decorator
        class Obj:
            def __init__(self):
                self.alert = sw.Alert()
                self.btn = sw.Btn()

            @su.loading_button(debug=False)
            def func1(self, *args):
                return 1 / 0

            @su.loading_button(debug=True)
            def func2(self, *args):
                return 1 / 0

            @su.loading_button(debug=False)
            def func3(self, *args):
                warnings.warn("toto")
                warnings.warn("sepal", SepalWarning)
                return 1

            @su.loading_button(debug=True)
            def func4(self, *args):
                warnings.warn("toto")
                warnings.warn("sepal", SepalWarning)
                return 1

        obj = Obj()

        # should only display error in the alert
        obj.func1(obj.btn, None, None)
        assert obj.btn.disabled is False
        assert obj.alert.type == "error"

        # should raise an error
        obj.alert.reset()
        with pytest.raises(Exception):
            obj.fun2(obj.btn, None, None)
        assert obj.btn.disabled is False
        assert obj.alert.type == "error"

        # should only display the sepal warning
        obj.alert.reset()
        obj.func3(obj.btn, None, None)
        assert obj.btn.disabled is False
        assert obj.alert.type == "warning"
        assert "sepal" in obj.alert.children[1].children[0]
        assert "toto" not in obj.alert.children[1].children[0]

        # should raise warnings
        obj.alert.reset()
        with warnings.catch_warnings(record=True) as w_list:
            obj.func4(obj.btn, None, None)
        assert obj.btn.disabled is False
        assert obj.alert.type == "warning"
        assert "sepal" in obj.alert.children[1].children[0]
        assert "toto" not in obj.alert.children[1].children[0]
        msg_list = [w.message.args[0] for w in w_list]
        assert any("sepal" in s for s in msg_list)
        assert any("toto" in s for s in msg_list)

        return

    def test_to_colors(self):

        # setup the same color in several formats
        colors = {
            "hex": "#b8860b",
            "rgb": (0.7215686274509804, 0.5254901960784314, 0.043137254901960784),
            "rgb_int": (184, 134, 11),
            "gee_hex": "b8860b",
            "text": "darkgoldenrod",
        }

        for c in colors.values():
            res = su.to_colors(c)
            assert res == colors["hex"]

        # test that a fake one return black
        res = su.to_colors("toto")
        assert res == "#000000"

        return

    def test_switch(self, capsys):

        # create a fake object that uses the decorator
        class Obj:
            def __init__(self):
                self.valid = True
                self.select = v.Select(disabled=False)
                self.select2 = v.Select(disabled=False)

                # apply on non string
                self.func4 = su.switch("disabled", on_widgets=[self.select])(self.func4)

            # apply the widget on the object itself
            @su.switch("valid")
            def func1(self, *args):
                return True

            # apply the widget on members of the object
            @su.switch("disabled", on_widgets=["select", "select2"])
            def func2(self, *args):
                return True

            # apply it on a non existent widget
            @su.switch("niet", on_widgets=["fake_widget"])
            def func3(self, *args):
                return True

            def func4(self, *args):
                return True

            # apply on a error func with debug = True
            @su.switch("valid", debug=True)
            def func5(self, *args):
                return 1 / 0

            # apply the switch with a non matching number of targets
            @su.switch("disabled", on_widgets=["select", "select2"], targets=[True])
            def func6(self, *args):
                return True

        obj = Obj()

        # assert
        obj.func1()
        assert obj.valid is True

        obj.func2()
        assert obj.select.disabled is False
        assert obj.select2.disabled is False

        with pytest.raises(Exception):
            obj.func3()

        with pytest.raises(Exception):
            obj.func4()

        with pytest.raises(Exception):
            obj.func5()

        with pytest.raises(IndexError):
            obj.func6()

        return

    def test_next_string(self):

        # Arrange
        input_string = "name"
        output_string = "name_1"

        # Act - assert
        assert su.next_string(input_string) == output_string
        assert su.next_string(input_string)[-1].isdigit()
        assert su.next_string("name_1") == "name_2"

        return

    def test_set_config_locale(self):

        # remove any config file that could exist
        if config_file.is_file():
            config_file.unlink()

        # create a config_file with a set language
        locale = "fr-FR"
        su.set_config_locale(locale)

        config = ConfigParser()
        config.read(config_file)
        assert "sepal-ui" in config.sections()
        assert config["sepal-ui"]["locale"] == locale

        # change an existing locale
        locale = "es-CO"
        su.set_config_locale(locale)
        config.read(config_file)
        assert config["sepal-ui"]["locale"] == locale

        # destroy the file again
        config_file.unlink()

        return

    def test_set_config_theme(self):

        # remove any config file that could exist
        if config_file.is_file():
            config_file.unlink()

        # create a config_file with a set language
        theme = "dark"
        su.set_config_theme(theme)

        config = ConfigParser()
        config.read(config_file)
        assert "sepal-ui" in config.sections()
        assert config["sepal-ui"]["theme"] == theme

        # change an existing locale
        theme = "light"
        su.set_config_theme(theme)
        config.read(config_file)
        assert config["sepal-ui"]["theme"] == theme

        # destroy the file again
        config_file.unlink()

        return

    def test_set_style(self):

        # test every legit type
        for t in TYPES:
            assert t == su.set_type(t)

        # test the fallback to info
        with pytest.warns(SepalWarning):
            res = su.set_type("toto")
            assert res == "info"

        return

    @su.need_ee
    def test_geojson_to_ee(self):

        # create a point list
        points = [sg.Point(i, i + 1) for i in range(4)]
        d = {"col1": [str(i) for i in range(len(points))], "geometry": points}
        gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")
        gdf_buffer = gdf.copy()
        gdf_buffer.geometry = gdf_buffer.buffer(0.5)

        # test a featurecollection
        ee_feature_collection = su.geojson_to_ee(gdf_buffer.__geo_interface__)
        assert isinstance(ee_feature_collection, ee.FeatureCollection)
        assert ee_feature_collection.size().getInfo() == len(points)

        # test a feature
        feature = gdf_buffer.iloc[:1].__geo_interface__["features"][0]
        ee_feature = su.geojson_to_ee(feature)
        assert isinstance(ee_feature, ee.Geometry)

        # test a single point
        point = sg.Point(0, 1)
        point = gdf.iloc[:1].__geo_interface__["features"][0]
        ee_point = su.geojson_to_ee(point)
        assert isinstance(ee_point, ee.Geometry)
        assert ee_point.coordinates().getInfo() == [0, 1]

        # test a badly shaped dict
        dict_ = {"type": ""}  # minimal feature from __geo_interface__
        with pytest.raises(ValueError):
            su.geojson_to_ee(dict_)

        return

    def test_check_input(self):

        with pytest.raises(ValueError, match="The value has not been initialized"):
            su.check_input(None)

        with pytest.raises(ValueError, match="toto"):
            su.check_input(None, "toto")

        res = su.check_input(1)
        assert res is True

        # test lists
        res = su.check_input([range(2)])
        assert res is True

        # test empty list
        with pytest.raises(ValueError):
            su.check_input([])

        return
