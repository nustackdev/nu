# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Loomi"
copyright = "2025, Gor Arakelyan"
author = "Gor Arakelyan"
release = "0.2.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autosectionlabel",
    "m2r2",
    "sphinx_click",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

html_theme_options = {
    "source_repository": "https://github.com/loomi-lab/loomi/",
    "source_branch": "main",
    "source_directory": "docs/",
}

templates_path = ["_templates"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_logo = "_static/images/logo.png"
html_favicon = "_static/images/logo.png"

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_default_options = {"exclude-members": "__init__, __repr__, __weakref__"}

source_suffix = [".rst", ".md"]

with open("rst_prolog.rst", "r") as prolog_file:
    rst_prolog = prolog_file.read()
