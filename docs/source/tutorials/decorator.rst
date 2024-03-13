Decorators
==========

When developing a user interface, some common tasks are repetitive and important for the user experience: trigger an action over some widgets when a method is called, catch errors within some method execution and avoid users to click over other buttons while the main process is running.

In this tutorial, you will be introduced to the sepal_ui decorators and how they will help you tackle that tasks by taking the following topics:

-   Description: what is a decorator and what is its basic syntax?
-   Types: interactive and validation.
-   Use cases: when and where to use decorators? practical example.

Description
-----------

The sepal_ui decorators are a simple and useful way to improve the readability and functionality of your code. A decorator is a function that allows you to add extra functionality to an existing object (such as a function) without modifying its structure: it takes a function as an argument, adds some functionality (could be after and/or before), and returns it.

Its basic syntax is to write :code:`@decorator_name` with its optional arguments at the top of a function definition, just as is shown below:

.. code-block:: python

   @decorator(**kwargs)
   def method(self):
      return

In some specific cases (keep reading), this syntax might vary, and you won't be able to use the :code:`@` on top of the definition, the method has to be decorated manually in the :code:`__init__` function, just as is shown below:

.. code-block:: python

  def __init__(self):
    # ...
    self.method = su.loading_button(alert=w_alert_name, button=w_button_name)(self.method)

    # ...
  def method(self):
     do_something()

.. note::

   Not all the decorators receive arguments, as we will see in the following sections, those are optional and will depend on the decorator objectives.

Decorator types
---------------

In the sepal_ui we have two types of decorators:

-  Interactive: those that will trigger traits over objects, and
-  Validation: those that will validate the minimum requirements to run a method/function.

.. note::

    This classification is only valid for this tutorial scope and might not be applicable for external use.

Interactive
^^^^^^^^^^^

The interactive decorators are intended to be used inside a class inheriting from ipyvuetify widgets (such the SepalWdigets). The purpose of them is to trigger an event before, and after the execution of a method.

-   :code:`loading_button`: is used to capture :code:`Exceptions` and :code:`warnings` from the method and display them into the alert widget, as well as toggle loading the button which trigger the event.
-   :code:`switch`: is used to switch (on/off) any boolean parameter of a ipyvuetify or SepalWidget class.

Validation
^^^^^^^^^^

The validation decorators are useful when you want to perform some test prior the use of a method or a function, the decorator will perform a validation tests and if everything is ok, the function/method is executed, otherwise an exception is raised.

-   :code:`need_ee`: is used to validate and check if the object requires EE binding, and it will trigger an exception if the connection is not possible.

Use cases
---------

Imagine that you are developing a tile that requires to be connected to your GEE account, request your root asset id's and fill up a selection widget. To improve the user experience, you also want the following:

-   Validate if the SEPAL user is connected to Google Earth Engine.
-   Create an alert and display errors (if there is any).
-   Turn on/off the :code:`loading` and :code:`disabled` parameters of the selection widget while the process is running.

Let's import the required modules. All the decorators are stored in the utils module.

.. code:: python

    import ee
    from time import sleep
    import ipyvuetify as v
    import sepal_ui.sepalwidgets as sw
    import sepal_ui.scripts.utils as su
    import sepal_ui.scripts.decorator as sd


Now, create a custom tile with all the elements that we will require to be displayed in our interface, as well as the events that we want to trigger.

.. note::

    We have also created a check box to raise exception to see how the decorator captures them.

.. code:: python

    class CustomTile(v.Card):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.btn = sw.Btn('Get assets')
            self.btn_on_card = sw.Btn('On card')
            self.w_raise = v.Checkbox(label='raise exception?', v_model=None)

            self.alert = sw.Alert().show()
            self.w_select = v.Select()

            self.children = [
                self.w_raise,
                self.w_select,
                self.btn,
                self.btn_on_card,
                self.alert
            ]

            self.btn.on_event('click', self.get_items_event)
            self.btn_on_card.on_event('click', self.on_card_event)


It's time to use the decorators in the class methods. For this example, we will have two events, the :code:`get_items_event` that will fill up the :code:`selection` widget items with the GEE root assets ids, and the :code:`on_card_event` that will do nothing more than wait for two seconds.

.. warning::

    The :code:`loading_button` decorator can only be used with the :code:`@decorator` syntax if its optional arguments (alert and button) are named as 'alert' and 'btn', otherwise the decoration has to follow this syntax in the :code:`__init__` class method...


.. code-block:: python

        @sd.loading_button()
        @sd.switch('loading', 'disabled', on_widgets=['w_select'])
        def get_items_event(self):
            """request GEE items"""

            self.children = self.request_items()

        @sd.switch('loading', 'disabled')
        def on_card_event(self):

            sleep(2)

        @sd.need_ee
        def request_items(self):
            """Connect to gee and request the root assets id's"""

            folder = f"projects/{ee.data._cloud_api_user_project}/assets"
            return [
                asset["id"]
                for asset
                in ee.data.listAssets({"parent": folder})["assets"]
            ]

And finally, when putting all together, you will end with a simple coded interface that has useful behaviors to the end user.


.. figure:: ../_image/tutorials/decorator/decorators-example.gif
   :alt: decorator example
   :align: center
