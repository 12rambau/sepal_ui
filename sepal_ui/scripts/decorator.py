"""Decorators used in sepal-ui.

used for multiple use-case sucha as (but not limited):
- catch errors in scripts to avoid Voila app freeze
- redirect error to a specific Alert object
- Initialize EE
- debug widgets
...
"""

import json
import os
import warnings
from functools import wraps
from itertools import product
from pathlib import Path
from typing import Any, Callable, List, Optional
from warnings import warn

import ee
import httplib2
import ipyvuetify as v
from deprecated.sphinx import versionadded

from sepal_ui.message import ms

# from sepal_ui.scripts.utils import init_ee
from sepal_ui.scripts.warning import SepalWarning

################################################################################
# This method is a copy of the one from utils. It should stay there
# as long as there is deprecation warning in utils, we cannot import it due to a circular
# import. This method should then be removed in v3.0 when sd won't be imported by utils
#


def init_ee() -> None:
    r"""Initialize earth engine according using a token.

    THe environment used to run the tests need to have a EARTHENGINE_TOKEN variable.
    The content of this variable must be the copy of a personal credential file that you can find on your local computer if you already run the earth engine command line tool. See the usage question for a github action example.

    - Windows: ``C:\Users\USERNAME\\.config\\earthengine\\credentials``
    - Linux: ``/home/USERNAME/.config/earthengine/credentials``
    - MacOS: ``/Users/USERNAME/.config/earthengine/credentials``

    Note:
        As all init method of pytest-gee, this method will fallback to a regular ``ee.Initialize()`` if the environment variable is not found e.g. on your local computer.
    """
    credential_folder_path = Path.home() / ".config" / "earthengine"
    credential_file_path = credential_folder_path / "credentials"

    if "EARTHENGINE_TOKEN" in os.environ and not credential_file_path.exists():

        # write the token to the appropriate folder
        ee_token = os.environ["EARTHENGINE_TOKEN"]
        credential_folder_path.mkdir(parents=True, exist_ok=True)
        credential_file_path.write_text(ee_token)

    # Extract the project name from credentials
    _credentials = json.loads(credential_file_path.read_text())
    project_id = os.environ.get(
        "EARTHENGINE_PROJECT",
        _credentials.get("project_id", _credentials.get("project", None)),
    )

    if not project_id:
        raise NameError(
            "The project name cannot be detected. "
            "Please set the EARTHENGINE_PROJECT environment variable. "
            "Or authenticate using `earthengine set_project project_name`."
        )

    # if the user is in local development the authentication should
    # already be available
    ee.Initialize(project=project_id, http_transport=httplib2.Http())


################################################################################


@versionadded(version="3.0", reason="moved from utils to a dedicated module")
def catch_errors(alert: Optional[v.Alert] = None, debug: Optional[bool] = None) -> Any:
    """Decorator to execute try/except sentence and catch errors in the alert message.

    If debug is True then the error is raised anyway.

    Args:
        alert: Alert to display errors
        debug: Whether to raise the error or not, default to false

    Returns:
        The return statement of the decorated method
    """
    if debug is not None:
        warn("debug argument defaults to `True`. It will be removed in v3.2")

    def decorator_alert_error(func):
        @wraps(func)
        def wrapper_alert_error(self, *args, **kwargs):
            # Change name of variable to assign it again in this scope
            # check if alert exist in the parent object if alert is not set manually
            assert hasattr(self, "alert") or alert, ms.decorator.no_alert
            alert_ = self.alert if not alert else alert
            alert_.reset()

            # try to execute the method
            value = None
            try:
                # Catch warnings in the process function
                with warnings.catch_warnings(record=True) as w_list:
                    value = func(self, *args, **kwargs)

                # Check if there are warnings in the function and append them
                # Use append msg as several warnings could be triggered
                if w_list:
                    # split the warning list
                    w_list_sepal = [
                        w for w in w_list if isinstance(w.message, SepalWarning)
                    ]

                    # display the sepal one
                    ms_list = [
                        f"{w.category.__name__}: {w.message.args[0]}"
                        for w in w_list_sepal
                    ]
                    [alert_.append_msg(ms, type_="warning") for ms in ms_list]

                    def custom_showwarning(w):
                        return warnings.showwarning(
                            message=w.message,
                            category=w.category,
                            filename=w.filename,
                            lineno=w.lineno,
                            line=w.line,
                        )

                    [custom_showwarning(w) for w in w_list]

            except Exception as e:
                alert_.add_msg(f"{e}", type_="error")
                raise e

            return value

        return wrapper_alert_error

    return decorator_alert_error


@versionadded(version="3.0", reason="moved from utils to a dedicated module")
def need_ee(func: Callable) -> Any:
    """Decorator to execute check if the object require EE binding.

    Trigger an exception if the connection is not possible.

    Args:
        func: the object on which the decorator is applied

    Returns:
        The return statement of the decorated method
    """

    @wraps(func)
    def wrapper_ee(*args, **kwargs):
        # try to connect to ee
        try:
            init_ee()
        except Exception:
            raise Exception("This function needs an Earth Engine authentication")

        return func(*args, **kwargs)

    return wrapper_ee


@versionadded(version="3.0", reason="moved from utils to a dedicated module")
def loading_button(
    alert: Optional[v.Alert] = None,
    button: Optional[v.Btn] = None,
    debug: Optional[bool] = None,
) -> Any:
    """Decorator to execute try/except sentence and toggle loading button object.

    Designed to work within the Tile object, or any object that have a self.btn and self.alert set.

    Args:
        button: Toggled button
        alert: the alert to display the error message
        debug: Whethers or not the exception should stop the execution. default to False

    Returns:
        The return statement of the decorated method
    """
    if debug is not None:
        warn("debug argument defaults to `True`. It will be removed in v3.2")

    def decorator_loading(func):
        @wraps(func)
        def wrapper_loading(self, *args, **kwargs):
            # set btn and alert
            # Change name of variable to assign it again in this scope
            # check if they exist in the parent object if alert is not set manually
            assert hasattr(self, "alert") or alert, ms.decorator.no_alert
            assert hasattr(self, "btn") or button, ms.decorator.no_button
            button_ = self.btn if not button else button
            alert_ = self.alert if not alert else alert

            # Clean previous loaded messages in alert
            alert_.reset()

            button_.toggle_loading()  # Start loading

            value = None

            try:
                # run the function using the catch_error decorator
                value = catch_errors(alert=alert_)(func)(self, *args, **kwargs)

            except Exception as e:
                button_.toggle_loading()
                raise e

            # normal behavior where we stop the loading state after the function is executed
            button_.toggle_loading()

            return value

        return wrapper_loading

    return decorator_loading


@versionadded(version="3.0", reason="moved from utils to a dedicated module")
def switch(
    *params, debug: bool = True, on_widgets: List[str] = [], targets: List[bool] = []
) -> Any:
    r"""Decorator to switch the state of input boolean parameters on class widgets or the class itself.

    If on_widgets is defined, it will switch the state of every widget
    parameter, otherwise it will change the state of the class (self). You can also set
    two decorators on the same function, one could affect the class and other the widgets.

    Args:
        \*params: any boolean parameter of a SepalWidget.
        debug: Whether trigger or not an Exception if the decorated function fails.
        on_widgets: List of widget names into the class
        targets: list of the target value (value that will be set on switch. default to the inverse of the current state.

    Returns:
        The return statement of the decorated method
    """

    def decorator_switch(func):
        @wraps(func)
        def wrapper_switch(self, *args, **kwargs):
            widgets_len = len(on_widgets)
            targets_len = len(targets)

            # sanity check on targets and on_widgets
            if widgets_len and targets_len:
                if widgets_len != targets_len:
                    raise IndexError(
                        f'the length of "on_widgets" ({widgets_len}) is different from the length of "targets" ({targets_len})'
                    )

            # create the list of target values based on the target list
            # or the initial values of the widgets params
            # The first one is taken as reference
            if not targets_len:
                w = getattr(self, on_widgets[0]) if widgets_len else self
                targets_ = [bool(getattr(w, p)) for p in params]
            else:
                targets_ = targets

            if widgets_len:
                # Verify that the input elements are strings
                wrong_types = [
                    (w, type(w)) for w in on_widgets if not isinstance(w, str)
                ]

                if len(wrong_types):
                    errors = [
                        f"Received:{w_type} for widget: {w}."
                        for w, w_type in wrong_types
                    ]

                    raise TypeError(
                        f"All on_widgets list elements has to be strings. [{' '.join(errors)}]"
                    )

                missing_widgets = [w for w in on_widgets if not hasattr(self, w)]

                if missing_widgets:
                    raise Exception(
                        f"The provided {missing_widgets} widget(s) does not exist in the current class"
                    )

                def w_assign(bool_targets):
                    params_targets = [
                        (p, bool_targets[i]) for i, p in enumerate(params)
                    ]

                    for w_name, p_t in product(on_widgets, params_targets):
                        param, target = p_t
                        widget = getattr(self, w_name)
                        setattr(widget, param, target)

            else:

                def w_assign(bool_targets):
                    for i, p in enumerate(params):
                        setattr(self, p, bool_targets[i])

            # assgn the parameters to the target inverse
            w_assign([not t for t in targets_])

            # execute the function and catch errors
            try:
                func(self, *args, **kwargs)

            except Exception as e:
                if debug:
                    w_assign(targets_)
                    raise e

            # reassign the parameters to the targets
            w_assign(targets_)

        return wrapper_switch

    return decorator_switch
