import ipyvuetify as v

from sepal_ui.sepalwidgets.sepalwidget import SepalWidget
from ..scripts import utils

__all__ = ["Btn", "DownloadBtn"]


class Btn(v.Btn, SepalWidget):
    """
    Custom process Btn filled with the provided text.
    the color will be defaulted to 'primary' and can be changed afterward according to your need

    Args:
        text (str, optional): the text to display in the btn
        icon (str, optional): the full name of any mdi-icon
        kwargs (dict, optional): any parameters from v.Btn. if set, ['children'] will be overwritten.

    Attributes:
        v_icon (v.icon): the icon in the btn
    """

    def __init__(self, text="Click", icon="", **kwargs):

        # create the default v_icon
        self.v_icon = v.Icon(left=True, children=[icon])

        # set the default parameters
        kwargs["color"] = kwargs.pop("color", "primary")
        kwargs["children"] = [self.v_icon, text]

        # call the constructor
        super().__init__(**kwargs)

    def set_icon(self, icon):
        """
        set a new icon

        Args:
            icon (str): the full name of a mdi-icon

        Return:
            self
        """
        self.v_icon.children = [icon]

        return self

    def toggle_loading(self):
        """
        Jump between two states : disabled and loading - enabled and not loading

        Return:
            self
        """
        self.loading = not self.loading
        self.disabled = self.loading

        return self


class DownloadBtn(v.Btn, SepalWidget):
    """
    Custom download Btn filled with the provided text.
    the download icon is automatically embeded and green.
    The btn only accepts absolute links. if non is provided then the btn stays disabled

    Args:
        text (str): the message inside the btn
        path (str, optional): the absolute to a downloadable content
        args (dict, optional): any parameter from a v.Btn. if set, ['children', 'target'] will be overwritten.
    """

    def __init__(self, text, path="#", **kwargs):

        # create a download icon
        v_icon = v.Icon(left=True, children=["mdi-download"])

        # set default parameters
        kwargs["class_"] = kwargs.pop("class_", "ma-2")
        kwargs["xs5"] = kwargs.pop("xs5", True)
        kwargs["color"] = kwargs.pop("color", "success")
        kwargs["children"] = [v_icon, text]
        kwargs["target"] = "_blank"

        # call the constructor
        super().__init__(**kwargs)

        # create the URL
        self.set_url(path)

    def set_url(self, path="#"):
        """
        Set the URL of the download btn. and unable it.
        If nothing is provided the btn is disabled

        Args:
            path (str): the absolute path to a downloadable content

        Return:
            self
        """

        if utils.is_absolute(path):
            url = path
        else:
            url = utils.create_download_link(path)

        self.href = url
        self.disabled = path == "#"

        return self
