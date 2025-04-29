"""
MDX renderer for the Python API Reference Generator.

This module provides functionality to render Python module information
as MDX documentation.
"""

from __future__ import annotations

import html
import logging
import sys
from typing import Any, List

from ..config.models import RenderingConfig
from ..core.models import ClassInfo, FunctionInfo, ModuleInfo
from .components import (  # Cards; Callouts; Tabs; Code
    enhance_code_blocks,
    render_class_cards,
    render_class_definition,
    render_deprecation_callout,
    render_example,
    render_examples_tabs,
    render_function_cards,
    render_function_signature,
    render_inheritance_callout,
    render_method_signature,
    render_method_tabs,
    render_module_cards,
    render_note_callout,
    render_signature,
    render_source_code,
    render_summary_callout,
    render_tabs,
    render_variable_cards,
    render_warning_callout,
)

logger = logging.getLogger(__name__)


class MDXRenderer:
    """Renders module information into MDX format."""

    def __init__(self, config: RenderingConfig):
        """
        Initialize the MDX renderer.

        Args:
            config: Configuration for rendering
        """
        self.config = config
        self.emojis = config.emojis
        self.section_order = config.section_order
        self.include_source_code = config.include_source_code

    def render_module(self, module_info: ModuleInfo) -> str:  # noqa: C901
        """
        Render a module to MDX format.

        Args:
            module_info: Module information to render

        Returns:
            MDX content as a string
        """
        logger.debug(f"Rendering module: {module_info.name}")

        result: List[str] = []

        # Add frontmatter
        page_title = module_info.name.split(".")[-1]  # Get the last part of the module name
        is_index = page_title == "index" or page_title == "__init__"

        # Start frontmatter
        result.append("---\n")
        result.append(f"title: {page_title}\n")
        result.append(f"sidebarTitle: {self.emojis['module']} {page_title}\n")
        if is_index:
            result.append("asIndexPage: true\n")
        result.append("---\n\n")

        # Add Nextra component imports
        result.append("import { Cards, Callout, Tabs } from 'nextra/components'\n\n")

        # Module header with emoji
        result.append(f"# {self.emojis['module']} `{module_info.name}` Reference\n\n")

        # Module docstring
        if module_info.docstring:
            # Add summary in callout
            if module_info.docstring.summary:
                result.append(render_summary_callout(module_info.docstring.summary))

            # Add extended description
            if module_info.docstring.description:
                result.append(f"{module_info.docstring.description}\n\n")

            # Add deprecation warning if present
            result.append(render_deprecation_callout(module_info.docstring))

        # Determine section order
        sections = []
        if module_info.submodules:
            sections.append(("Modules", self._render_submodules_section(module_info)))
        if module_info.classes:
            sections.append(("Classes", self._render_classes_section(module_info)))
        if module_info.functions:
            sections.append(("Functions", self._render_functions_section(module_info)))
        # if module_info.variables:
        #     sections.append(("Variables", self._render_variables_section(module_info)))

        # Sort sections according to config
        ordered_sections = []
        for section_name in self.section_order:
            for name, content in sections:
                if name == section_name:
                    ordered_sections.append((name, content))
                    break

        # Add any remaining sections not in the order
        section_names = set(name for name, _ in ordered_sections)
        for name, content in sections:
            if name not in section_names:
                ordered_sections.append((name, content))

        # Add ordered sections to result
        for _, content in ordered_sections:
            result.append(content)

        # Add source code if requested
        if self.include_source_code:
            try:
                module_obj = sys.modules.get(module_info.name)
                if module_obj:
                    result.append("## Source Code\n\n")
                    result.append(render_source_code(module_obj))
            except Exception as e:
                logger.warning(f"Failed to include source code for module {module_info.name}: {e}")

        # Enhance code blocks
        content = "".join(result)
        return enhance_code_blocks(content)

    def _render_submodules_section(self, module_info: ModuleInfo) -> str:
        """Render the submodules section."""
        return render_module_cards(module_info.submodules)

    def _render_classes_section(self, module_info: ModuleInfo) -> str:
        """Render the classes section."""
        result = []

        # Quick navigation cards for classes
        result.append(render_class_cards(module_info.classes))

        # Detailed class documentation
        if module_info.classes:
            result.append("---\n\n")
            for class_info in sorted(module_info.classes, key=lambda c: c.name):
                result.append(self._render_class(class_info))

        return "".join(result)

    def _render_functions_section(self, module_info: ModuleInfo) -> str:
        """Render the functions section."""
        result = []

        # Quick navigation cards for functions
        result.append(render_function_cards(module_info.functions))

        # Detailed function documentation
        if module_info.functions:
            result.append("---\n\n")
            for function_info in sorted(module_info.functions, key=lambda f: f.name):
                result.append(self._render_function(function_info))

        return "".join(result)

    def _render_variables_section(self, module_info: ModuleInfo) -> str:
        """Render the variables section."""
        result = []

        # Quick navigation cards for variables
        result.append(render_variable_cards(module_info.variables))

        # Split into constants and variables
        constants = [v for v in module_info.variables if v.is_constant]
        variables = [v for v in module_info.variables if not v.is_constant]

        # Document constants
        if constants:
            result.append("<a id='constants'></a>\n\n")
            result.append("### Constants\n\n")
            result.append("| Name | Type | Value | Description |\n")
            result.append("| ---- | ---- | ----- | ----------- |\n")
            for var_info in sorted(constants, key=lambda v: v.name):
                value_str = self._get_value_str(var_info.value)
                desc = var_info.docstring or ""
                result.append(
                    f"| `{var_info.name}` | `{var_info.type_name}` | {value_str} | {desc} |\n"
                )
            result.append("\n")

        # Document variables
        if variables:
            result.append("<a id='variables'></a>\n\n")
            result.append("### Variables\n\n")
            result.append("| Name | Type | Value | Description |\n")
            result.append("| ---- | ---- | ----- | ----------- |\n")
            for var_info in sorted(variables, key=lambda v: v.name):
                value_str = self._get_value_str(var_info.value)
                desc = var_info.docstring or ""
                result.append(
                    f"| `{var_info.name}` | `{var_info.type_name}` | {value_str} | {desc} |\n"
                )
            result.append("\n")

        return "".join(result)

    def _render_class(self, class_info: ClassInfo) -> str:  # noqa: C901
        """Render a class to MDX format."""
        result: List[str] = []

        # Class header with emoji and anchor
        result.append(f"<a id='{class_info.name.lower()}'></a>\n\n")
        result.append(f"## {class_info.name} {self.emojis['class']}\n\n")

        # Class inheritance in callout
        if class_info.bases:
            result.append(render_inheritance_callout(class_info))

        # Class docstring
        if class_info.docstring:
            # Add summary
            if class_info.docstring.summary:
                result.append(f"{class_info.docstring.summary}\n\n")

            # Add extended description
            if class_info.docstring.description:
                result.append(f"{class_info.docstring.description}\n\n")

            # Add deprecation warning if present
            result.append(render_deprecation_callout(class_info.docstring))

        # Class definition
        result.append(render_class_definition(class_info.name, class_info.bases))

        # Document class attributes
        if class_info.attributes:
            result.append("### Class Attributes\n\n")
            result.append("| Name | Type | Value | Description |\n")
            result.append("| ---- | ---- | ----- | ----------- |\n")

            for attr in sorted(class_info.attributes, key=lambda a: a.name):
                value_str = self._get_value_str(attr.value)
                desc = attr.docstring or ""
                result.append(f"| `{attr.name}` | `{attr.type_name}` | {value_str} | {desc} |\n")
            result.append("\n")

        # Document class properties
        if class_info.properties:
            result.append("### Properties\n\n")
            result.append("| Name | Description |\n")
            result.append("| ---- | ----------- |\n")

            for prop in sorted(class_info.properties, key=lambda p: p.name):
                summary = prop.docstring.summary if prop.docstring else ""
                result.append(f"| `{prop.name}` | {summary} |\n")
            result.append("\n")

            # Add detailed property documentation if needed
            if any(
                prop.docstring and (prop.docstring.description or prop.docstring.examples)
                for prop in class_info.properties
            ):
                result.append("#### Property Details\n\n")
                for prop in sorted(class_info.properties, key=lambda p: p.name):
                    if prop.docstring and (prop.docstring.description or prop.docstring.examples):
                        result.append(f"##### `{prop.name}`\n\n")
                        if prop.docstring.description:
                            result.append(f"{prop.docstring.description}\n\n")
                        if prop.docstring.examples:
                            result.append("**Example:**\n\n")
                            result.append(f"```python\n{prop.docstring.examples[0].code}\n```\n\n")

        # Document methods with tab interface
        if class_info.methods:
            result.append("### Methods\n\n")

            # If few methods, use simple list
            if len(class_info.methods) <= 3:
                for method_info in sorted(class_info.methods, key=lambda m: m.name):
                    result.append(self._render_method(method_info, in_tab=False))
            # If many methods, use tabs
            else:
                # Group methods by category
                normal_methods = []
                special_methods = []
                dunder_methods = []

                for method in class_info.methods:
                    if method.name.startswith("__") and method.name.endswith("__"):
                        dunder_methods.append(method)
                    elif method.name.startswith("_"):
                        special_methods.append(method)
                    else:
                        normal_methods.append(method)

                # Add normal methods
                if normal_methods:
                    result.append(
                        render_method_tabs(
                            normal_methods, lambda m: self._render_method(m, in_tab=True)
                        )
                    )

                # Add special methods if showing private
                if special_methods and self.config.show_private:
                    result.append("#### Special Methods\n\n")
                    result.append(
                        render_method_tabs(
                            special_methods, lambda m: self._render_method(m, in_tab=True)
                        )
                    )

                # Add dunder methods if showing dunder
                if dunder_methods and self.config.show_dunder:
                    result.append("#### Magic Methods\n\n")
                    result.append(
                        render_method_tabs(
                            dunder_methods, lambda m: self._render_method(m, in_tab=True)
                        )
                    )

        # Add examples if available in class docstring
        if class_info.docstring and class_info.docstring.examples:
            result.append("### Examples\n\n")
            result.append(render_examples_tabs([e.code for e in class_info.docstring.examples]))

        # Add source code if requested
        if self.include_source_code:
            # Try to get the actual class object for source code
            try:
                module_parts = class_info.module.split(".")
                current_obj = __import__(module_parts[0])
                for part in module_parts[1:]:
                    current_obj = getattr(current_obj, part)
                class_obj = getattr(current_obj, class_info.name)

                result.append("### Source Code\n\n")
                result.append(render_source_code(class_obj))
            except Exception as e:
                logger.warning(f"Failed to include source code for class {class_info.name}: {e}")

        return "".join(result)

    def _render_function(self, function_info: FunctionInfo) -> str:
        """Render a function to MDX format."""
        result: List[str] = []

        # Function header with emoji and anchor
        result.append(f"<a id='{function_info.name.lower()}'></a>\n\n")
        result.append(f"## {function_info.name}() {self.emojis['function']}\n\n")

        # Function signature
        result.append(render_function_signature(function_info))

        # Function docstring
        if function_info.docstring:
            # Add summary
            if function_info.docstring.summary:
                result.append(f"{function_info.docstring.summary}\n\n")

            # Add extended description
            if function_info.docstring.description:
                result.append(f"{function_info.docstring.description}\n\n")

            # Add deprecation warning if present
            result.append(render_deprecation_callout(function_info.docstring))

            # Add parameters documentation
            if function_info.docstring.parameters:
                result.append("### Parameters\n\n")
                result.append("| Name | Type | Description | Default |\n")
                result.append("| ---- | ---- | ----------- | ------- |\n")

                # Get parameter info from signature
                param_defaults = {}
                param_types = {}

                for param in function_info.signature.parameters:
                    name = param["name"]
                    param_types[name] = param.get("annotation", "Any")
                    if param.get("has_default", False):
                        param_defaults[name] = param.get("default", "None")

                # Render parameters
                for name, param in function_info.docstring.parameters.items():
                    type_hint = param.type_hint or param_types.get(name, "Any")
                    default = param_defaults.get(name, "Required")

                    result.append(
                        f"| `{name}` | `{type_hint}` | {param.description} | `{default}` |\n"
                    )
                result.append("\n")

            # Add return documentation
            if function_info.docstring.returns:
                return_type = function_info.signature.return_type or "Any"

                result.append("### Returns\n\n")
                result.append(f"**Type:** `{return_type}`\n\n")
                result.append(f"{function_info.docstring.returns.description}\n\n")

            # Add exceptions documentation
            if function_info.docstring.exceptions:
                result.append("### Raises\n\n")
                result.append("| Exception | Description |\n")
                result.append("| --------- | ----------- |\n")

                for name, exc in function_info.docstring.exceptions.items():
                    result.append(f"| `{name}` | {exc.description} |\n")
                result.append("\n")

            # Add examples
            if function_info.docstring.examples:
                result.append("### Examples\n\n")
                if len(function_info.docstring.examples) == 1:
                    # Single example
                    result.append(
                        f"```python filename='example.py'\n{function_info.docstring.examples[0].code}\n```\n\n"
                    )
                else:
                    # Multiple examples
                    result.append(
                        render_examples_tabs([e.code for e in function_info.docstring.examples])
                    )

        # Add source code if requested
        if self.include_source_code:
            # Try to get the actual function object for source code
            try:
                module_parts = function_info.module.split(".")
                current_obj = __import__(module_parts[0])
                for part in module_parts[1:]:
                    current_obj = getattr(current_obj, part)
                func_obj = getattr(current_obj, function_info.name)

                result.append("### Source Code\n\n")
                result.append(render_source_code(func_obj))
            except Exception as e:
                logger.warning(
                    f"Failed to include source code for function {function_info.name}: {e}"
                )

        return "".join(result)

    def _render_method(self, method_info: FunctionInfo, in_tab: bool = False) -> str:  # noqa: C901
        """Render a method to MDX format."""
        result: List[str] = []

        # Method header - different formatting if in tab
        if in_tab:
            result.append(f"### {method_info.name}() {self.emojis['method']}\n\n")
        else:
            result.append(f"<a id='{method_info.name.lower()}'></a>\n\n")
            result.append(f"#### {method_info.name}() {self.emojis['method']}\n\n")

        # Method signature
        result.append(render_method_signature(method_info))

        # Method docstring
        if method_info.docstring:
            # Add summary
            if method_info.docstring.summary:
                result.append(f"{method_info.docstring.summary}\n\n")

            # Add extended description if in tab or significant
            if in_tab and method_info.docstring.description:
                result.append(f"{method_info.docstring.description}\n\n")

            # Add deprecation warning if present
            result.append(render_deprecation_callout(method_info.docstring))

            # Add parameters documentation
            if method_info.docstring.parameters:
                result.append("**Parameters:**\n\n")
                result.append("| Name | Type | Description | Default |\n")
                result.append("| ---- | ---- | ----------- | ------- |\n")

                # Get parameter info from signature
                param_defaults = {}
                param_types = {}

                for param in method_info.signature.parameters:
                    name = param["name"]
                    param_types[name] = param.get("annotation", "Any")
                    if param.get("has_default", False):
                        param_defaults[name] = param.get("default", "None")

                # Render parameters
                for name, param in method_info.docstring.parameters.items():
                    # Skip self/cls for instance/class methods
                    if (
                        name in ("self", "cls")
                        and (not method_info.is_static)
                        and name not in param_defaults
                    ):
                        continue

                    type_hint = param.type_hint or param_types.get(name, "Any")

                    # Use docstring default if available, otherwise use signature default
                    if hasattr(param, "default") and param.default:
                        default = param.default
                    else:
                        default = param_defaults.get(name, "Required")

                    result.append(
                        f"| `{name}` | `{type_hint}` | {param.description} | `{default}` |\n"
                    )
                result.append("\n")

            # Add return documentation
            if method_info.docstring.returns:
                return_type = method_info.signature.return_type or "Any"

                result.append(
                    f"**Returns:** `{return_type}` - {method_info.docstring.returns.description}\n\n"
                )

            # Add exceptions documentation
            if method_info.docstring.exceptions:
                result.append("**Raises:**\n\n")
                result.append("| Exception | Description |\n")
                result.append("| --------- | ----------- |\n")

                for name, exc in method_info.docstring.exceptions.items():
                    result.append(f"| `{name}` | {exc.description} |\n")
                result.append("\n")

            # Add examples if available (always include them regardless of tab view)
            if method_info.docstring.examples:
                result.append("**Example:**\n\n")
                for example in method_info.docstring.examples:
                    result.append(f"```python\n{example.code}\n```\n\n")

        # Add source code if in tab and requested
        if in_tab and self.include_source_code:
            try:
                # Try to locate the method object
                module_parts = method_info.module.split(".")
                current_obj = __import__(module_parts[0])
                for part in module_parts[1:]:
                    try:
                        current_obj = getattr(current_obj, part)
                    except AttributeError:
                        break

                class_name = method_info.module.split(".")[-1]
                if hasattr(current_obj, class_name) and hasattr(
                    getattr(current_obj, class_name), method_info.name
                ):
                    method_obj = getattr(getattr(current_obj, class_name), method_info.name)
                    result.append("**Source Code:**\n\n")
                    result.append(render_source_code(method_obj))
            except Exception as e:
                logger.debug(f"Failed to include source code for method {method_info.name}: {e}")

        return "".join(result)

    def _get_value_str(self, value: Any) -> str:
        """Get a string representation of the value."""
        try:
            value_repr = repr(value)
            if len(value_repr) > 50:  # Truncate long values
                value_repr = value_repr[:47] + "..."
            return f"`{html.escape(value_repr)}`"
        except Exception:
            return "`[Unable to display value]`"
