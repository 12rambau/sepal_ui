"""sepal-ui configuration to save in the user machine.

To make applications more user-friendly sepal-ui save few parameters in a config file.
Currently we save the language and the theme so that it won't need to be reset every time.
"""

from configparser import ConfigParser
from pathlib import Path

config_file = Path.home() / ".sepal-ui-config"
config = ConfigParser()
"ConfigParser: the configuration object generated by sepal-ui based application to save parameters such as language or theme"
config.read(config_file)

# Set a default conifg when there is not file
if not config_file.exists():
    config.add_section("sepal-ui")
    config.set("sepal-ui", "theme", "dark")
    config.set("sepal-ui", "theme", "en")
    config.write(config_file.open("w"))
