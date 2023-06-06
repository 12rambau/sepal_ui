"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup ----------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../sepal_ui/bin"))

from sepal_ui import __author__, __version__  # noqa: E402

package_path = os.path.abspath("../..")
os.environ["PYTHONPATH"] = ":".join((package_path, os.environ.get("PYTHONPATH", "")))

DOC_DIR = Path(__file__).parent


# -- Project information -------------------------------------------------------

# General information about the project.
project = "sepal-ui"
copyright = f"2020-{datetime.now().year}, the sepal development team"
author = __author__

# The full version, including alpha/beta/rc tags
release = __version__


# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "m2r2",
    "jupyter_sphinx",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_favicon",
    "notfound.extension",
    "sphinxcontrib.autoprogram",
    "_extentions.line_break",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["**.ipynb_checkpoints"]

# to be able to read RST files
source_suffix = [".rst", ".md"]

# -- Load the images from the master sepal-doc ---------------------------------
urlretrieve(
    "https://raw.githubusercontent.com/openforis/sepal-doc/master/docs/source/_images/404-compass.png",
    "_image/dwn/404-compass.png",
)


# -- Options for HTML output ---------------------------------------------------

# Define the version we use for matching in the version switcher.
json_url = "https://sepal-ui.readthedocs.io/en/latest/_static/switcher.json"
version_match = os.environ.get("READTHEDOCS_VERSION")
# If READTHEDOCS_VERSION doesn't exist, we're not on RTD
# If it is an integer, we're in a PR build and the version isn't correct.
if not version_match or version_match.isdigit():
    # For local development, infer the version to latest
    release = "dev"
    version_match = "latest"
    json_url = "_static/switcher.json"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
html_last_updated_fmt = ""
html_theme_options = {
    "logo": {
        "text": "sepal-ui",
        "image_light": "https://raw.githubusercontent.com/openforis/sepal-doc/main/docs/source/_images/logo_light.png",
        "image_dark": "https://raw.githubusercontent.com/openforis/sepal-doc/main/docs/source/_images/logo_dark.png",
    },
    "use_edit_page_button": True,
    "show_prev_next": False,
    "switcher": {"json_url": json_url, "version_match": version_match},
    "navbar_start": ["navbar-logo", "version-switcher"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/12rambau/sepal_ui",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "Pypi",
            "url": "https://pypi.org/project/sepal-ui/",
            "icon": "fa-brands fa-python",
        },
    ],
}
html_context = {
    "github_user": "12rambau",
    "github_repo": "sepal_ui",
    "github_version": "master",
    "doc_path": "docs/source",
}

favicons = [
    # generic icons compatible with most browsers
    "favicon-32x32.png",
    "favicon-16x16.png",
    {"rel": "shortcut icon", "sizes": "any", "href": "favicon.ico"},
    # chrome specific
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    # apple icons
    {"rel": "mask-icon", "color": "#459db9", "href": "safari-pinned-tab.svg"},
    {"rel": "apple-touch-icon", "href": "apple-touch-icon.png"},
    # msapplications
    {"name": "msapplication-TileColor", "content": "#459db9"},
    {"name": "theme-color", "content": "#ffffff"},
    {"name": "msapplication-TileImage", "content": "mstile-150x150.png"},
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = ["css/custom.css", "css/icon.css"]

# -- Options for autosummary/autodoc output ------------------------------------
autosummary_generate = True
autoclass_content = "both"
autodoc_typehints = "description"

# -- Options for TODO ----------------------------------------------------------
todo_include_todos = True
