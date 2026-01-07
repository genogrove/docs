import os, sys
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "genogrove"
copyright = "2025, Richard. A. Schaefer"
author = "Richard. A. Schaefer"
release = "0.11.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# sys.path.insert(0, os.path.abspath("../repos/pygenogrove"))  # if you’ll import your python package

extensions = [
    "breathe",  # For C++ documentation via Doxygen
    "sphinx.ext.autodoc",  # For Python documentation from docstrings
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
]

# Breathe configuration for C++ docs
breathe_projects = {
    "genogrove": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../doxygen/xml")
    )
}
breathe_default_project = "genogrove"

# Breathe display options
breathe_default_members = ('members', 'undoc-members')
breathe_show_include = False

templates_path = ["_templates"]
exclude_patterns = []

# Autodoc settings for Python
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_theme_options = {
    "github_url": "https://github.com/genogrove/genogrove",
    "navbar_align": "left",
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["navbar-icon-links"],
    "navbar_persistent": ["search-button"],
    "show_toc_level": 3,
    "navigation_depth": 4,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/genogrove/genogrove",
            "icon": "fab fa-github-square",
        },
    ],
}

html_sidebars = {
    "**": ["sidebar-nav-bs"]
}
