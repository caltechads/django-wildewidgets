# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
# import sphinx_rtd_theme

import django
import os
import sys

sys.path.insert(0, os.path.abspath("../demo"))
os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"
django.setup()


# -- Project information -----------------------------------------------------

# the master toctree document
master_doc = "index"

project = "django-wildewidgets"
copyright = "2023, California Institute of Technology"  # pylint: disable=redefined-builtin
author = "Glenn Bach, Chris Malek"

from typing import Dict, Tuple, Optional  # noqa: E402


# The full version, including alpha/beta/rc tags
release = "1.1.7"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxcontrib.images",
    "sphinx.ext.intersphinx",
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

add_function_parentheses: bool = False
add_module_names: bool = False

autodoc_member_order = "groupwise"

# Make Sphinx not expand all our Type Aliases
autodoc_type_aliases: Dict[str, str] = {}

# the locations and names of other projects that should be linked to this one
intersphinx_mapping: Dict[str, Tuple[str, Optional[str]]] = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "http://docs.djangoproject.com/en/dev/",
        "http://docs.djangoproject.com/en/dev/_objects/",
    ),
}

# Configure the path to the Django settings module
django_settings = "demo.settings_docker"
# Include the database table names of Django models
django_show_db_tables = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_context = {
    "display_github": True,  # Integrate github
    "github_user": "caltech-imss-ads",  # Username
    "github_repo": "django-wildewidgets",  # Repo name
    "github_version": "main",  # Version
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "collapse_navigation": True,
    "navigation_depth": 3,
    "show_prev_next": False,
    "logo": {
        "image_light": "wildewidgets_logo.png",
        "image_dark": "wildewidgets_dark_mode_logo.png",
        "text": "Django-Wildewidgets",
    },
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/caltechads/django-wildewidgets",
            "icon": "fab fa-github-square",
            "type": "fontawesome",
        },
        {
            "name": "Demo",
            "url": "https://wildewidgets.caltech.edu",
            "icon": "fa fa-desktop",
            "type": "fontawesome",
        },
    ],
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_logo = "_static/wildewidgets.png"
html_favicon = "_static/favicon.ico"
