"""
Components module for the Python API Reference Generator.

This module provides rendering components for MDX documentation.
"""

from .callouts import (
    render_deprecation_callout,
    render_inheritance_callout,
    render_note_callout,
    render_summary_callout,
    render_warning_callout,
)
from .cards import (
    render_class_cards,
    render_function_cards,
    render_index_cards,
    render_module_cards,
    render_variable_cards,
)
from .code import (
    enhance_code_blocks,
    render_class_definition,
    render_example,
    render_function_signature,
    render_method_signature,
    render_signature,
    render_source_code,
)
from .tabs import render_examples_tabs, render_method_tabs, render_tabs

__all__ = [
    # Cards
    "render_module_cards",
    "render_class_cards",
    "render_function_cards",
    "render_variable_cards",
    "render_index_cards",
    # Callouts
    "render_summary_callout",
    "render_inheritance_callout",
    "render_deprecation_callout",
    "render_note_callout",
    "render_warning_callout",
    # Tabs
    "render_tabs",
    "render_method_tabs",
    "render_examples_tabs",
    # Code
    "render_signature",
    "render_function_signature",
    "render_method_signature",
    "render_class_definition",
    "render_example",
    "render_source_code",
    "enhance_code_blocks",
]
