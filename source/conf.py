import os
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "genogrove"
copyright = "2026, Richard. A. Schaefer"
author = "Richard. A. Schaefer"
release = "0.24.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# sys.path.insert(0, os.path.abspath("../repos/pygenogrove"))  # if you’ll import your python package

extensions = [
    "myst_parser",  # MyST Markdown parser
    "breathe",  # For C++ documentation via Doxygen
    "sphinx.ext.autodoc",  # For Python documentation from docstrings
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx_copybutton",  # Add copy button to code blocks
    "sphinx_design",  # Modern design components (cards, grids, tabs)
]

# Breathe configuration for C++ docs
breathe_projects = {
    "genogrove": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../doxygen/xml")
    )
}
breathe_default_project = "genogrove"

# Breathe display options
breathe_default_members = ("members", "undoc-members")
breathe_show_include = False

templates_path = ["_templates"]
exclude_patterns = []

# Breathe renders each Doxygen function declaration as a `cpp:function::`
# directive using only the visible signature. C++20 `requires`-clause overloads
# with identical signatures collapse to the same Sphinx declaration and trigger
# a duplicate-declaration warning — e.g. `key<T, D>::key()` (requires
# `default_initializable<D>`) and `key<T, void>::key()` (added in v0.24.4) both
# read as `inline key ()`. Both declarations are correct upstream; the warning
# is a tooling limitation.
suppress_warnings = ["cpp.duplicate_declaration"]

# MyST-Parser configuration
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",  # ::: for code blocks
    "deflist",  # Definition lists
    "fieldlist",  # Field lists
    "html_image",  # HTML images
    "linkify",  # Auto-link URLs
    "replacements",  # Text replacements
    "smartquotes",  # Smart quotes
    "strikethrough",  # ~~strikethrough~~
    "substitution",  # Variable substitution
    "tasklist",  # Task lists
]

myst_heading_anchors = 3  # Auto-generate anchors for headers up to level 3

# Copybutton configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"
copybutton_selector = "div.highlight pre"

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
    "show_nav_level": 2,
    "navigation_depth": 4,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/genogrove/genogrove",
            "icon": "fab fa-github-square",
            "type": "fontawesome",
        },
    ],
}

html_sidebars = {"**": ["sidebar-nav-bs"]}
