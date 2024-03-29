StateIcon
=========

:code:`StateIcon` is a custom widget to provide easy to use a mutable icon state: displaying a short description of the state with a tooltip and a descriptive color. This widget is intended to be linked with a :code:`SepalModel` trait, which will be in charge of changing the widget state. Here is an example:

.. jupyter-execute::
    :raises:
    :stderr:

    import ipyvuetify as v
    from traitlets import Unicode
    from sepal_ui import sepalwidgets as sw
    from sepal_ui.model import Model

    # correct colors for the documentation
    # set to dark in SEPAL by default
    v.theme.dark = False

    # Define a dummy model to manipulate externally the icon state
    class TestModel(Model):
        state_value = Unicode().tag(sync=True)

    model = TestModel()
    state_icon_a = sw.StateIcon(model, "state_value")

    state_icon_b = sw.StateIcon(model, "state_value")
    state_icon_b.value = "non_valid"

    sw.Col(children=[
        sw.Flex(xs12=True, children=[state_icon_a]),
        sw.Divider(class_="my-5"),
        sw.Flex(xs12=True, children=[state_icon_b]),
    ])

.. note::

    More information can be found `here <../modules/sepal_ui.sepalwidgets.html#sepal_ui.sepalwidgets.sepalwidget.StateIcon>`__.
