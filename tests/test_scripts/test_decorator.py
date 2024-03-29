"""Test the custom decorators."""

import warnings

import ee
import ipyvuetify as v
import pytest

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import decorator as sd
from sepal_ui.scripts.warning import SepalWarning


@pytest.mark.skipif(not ee.data._credentials, reason="GEE is not set")
def test_init_ee() -> None:
    """Check that ee can be initialized from sepal_ui."""
    # check that no error is raised
    sd.init_ee()

    return


def test_catch_errors() -> None:
    """Check the catch error decorator."""
    # create an external alert to test the wiring
    alert = sw.Alert()

    # create a fake object that uses the decorator
    class Obj:
        def __init__(self):
            self.alert = sw.Alert()
            self.btn = sw.Btn()

        @sd.catch_errors()
        def func0(self, *args):
            return 1 / 0

        @sd.catch_errors(alert=alert)
        def func1(self, *args):
            return 1 / 0

        @sd.catch_errors()
        def func2(self, *args):
            return "toto"

        @sd.loading_button()
        def func3(self, *args):
            warnings.warn("toto")
            warnings.warn("sepal", SepalWarning)
            return 1

        @sd.loading_button()
        def func4(self, *args):
            warnings.warn("toto")
            warnings.warn("sepal", SepalWarning)
            return 1

    obj = Obj()
    with pytest.raises(Exception):
        obj.func0()

    # should return an alert error in the the self alert widget
    assert obj.alert.type == "error"

    # Reset the alert to remove previous state
    assert obj.alert.reset()

    with pytest.raises(Exception):
        obj.func1()

    # should return an alert in the external alert widget
    assert alert.type == "error"

    # check when there's no error
    assert obj.alert.reset()
    value = obj.func2()
    assert value == "toto"
    assert obj.alert.type != "error"

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


def test_loading_button() -> None:
    """Check the loading decorator."""
    # create a fake object that uses the decorator
    class Obj:
        def __init__(self):
            self.alert = sw.Alert()
            self.btn = sw.Btn()

        @sd.loading_button()
        def func1(self, *args):
            return 1 / 0

        @sd.loading_button()
        def func2(self, *args):
            return 1 / 0

        @sd.loading_button()
        def func3(self, *args):
            return "toto"

    obj = Obj()

    # should only display error in the alert
    with pytest.raises(Exception):
        obj.func1(obj.btn, None, None)

    assert obj.btn.disabled is False
    assert obj.alert.type == "error"
    assert obj.btn.loading is False

    # func 3 shouldn't raise any error
    assert obj.alert.reset()
    value = obj.func3(obj.btn, None, None)

    assert value == "toto"
    assert obj.alert.type != "error"
    assert obj.btn.loading is False

    return


def test_switch() -> None:
    """Test the switch decorator."""
    # create a fake object that uses the decorator
    class Obj:
        def __init__(self):
            self.valid = True
            self.select = v.Select(disabled=False)
            self.select2 = v.Select(disabled=False)

            # apply on non string
            self.func4 = sd.switch("disabled", on_widgets=[self.select])(self.func4)

        # apply the widget on the object itself
        @sd.switch("valid")
        def func1(self, *args):
            return True

        # apply the widget on members of the object
        @sd.switch("disabled", on_widgets=["select", "select2"])
        def func2(self, *args):
            return True

        # apply it on a non existent widget
        @sd.switch("niet", on_widgets=["fake_widget"])
        def func3(self, *args):
            return True

        def func4(self, *args):
            return True

        # apply on a error func with debug = True
        @sd.switch("valid")
        def func5(self, *args):
            return 1 / 0

        # apply the switch with a non matching number of targets
        @sd.switch("disabled", on_widgets=["select", "select2"], targets=[True])
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
