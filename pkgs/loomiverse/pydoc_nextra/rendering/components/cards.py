"""
Card component rendering for the Python API Reference Generator.

This module provides functionality to render Nextra card components.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from ...core.models import ClassInfo, FunctionInfo, VariableInfo


def render_module_cards(modules: List[str]) -> str:
    """
    Render module cards for navigation.

    Args:
        modules: List of module names

    Returns:
        Rendered MDX content for module cards
    """
    if not modules:
        return ""

    lines = ["## Modules\n\n", "<Cards>\n"]

    for module_name in sorted(modules):
        short_name = module_name.split(".")[-1]
        href = [f"p_{part}" if part.startswith("_") else part for part in module_name.split(".")]
        lines.append(f'  <Cards.Card title="{short_name}" href="/api/{"/".join(href)}"/>\n')

    lines.append("</Cards>\n\n")

    return "".join(lines)


def render_class_cards(classes: List[ClassInfo]) -> str:
    """
    Render class cards for navigation.

    Args:
        classes: List of class info objects

    Returns:
        Rendered MDX content for class cards
    """
    if not classes:
        return ""

    lines = ["## Classes\n\n", "<Cards>\n"]

    for class_info in sorted(classes, key=lambda c: c.name):
        class_info.docstring.summary if class_info.docstring else ""
        lines.append(
            f'  <Cards.Card title="{class_info.name}" href="#{class_info.name.lower()}"/>\n'
        )

    lines.append("</Cards>\n\n")

    return "".join(lines)


def render_function_cards(functions: List[FunctionInfo]) -> str:
    """
    Render function cards for navigation.

    Args:
        functions: List of function info objects

    Returns:
        Rendered MDX content for function cards
    """
    if not functions:
        return ""

    lines = ["## Functions\n\n", "<Cards>\n"]

    for function_info in sorted(functions, key=lambda f: f.name):
        function_info.docstring.summary if function_info.docstring else ""
        lines.append(
            f'  <Cards.Card title="{function_info.name}()" href="#{function_info.name.lower()}"/>\n'
        )

    lines.append("</Cards>\n\n")

    return "".join(lines)


def render_variable_cards(variables: List[VariableInfo]) -> str:
    """
    Render variable cards for navigation.

    Args:
        variables: List of variable info objects

    Returns:
        Rendered MDX content for variable cards
    """
    if not variables:
        return ""

    # Split into constants and variables
    constants = [v for v in variables if v.is_constant]
    regular_vars = [v for v in variables if not v.is_constant]

    lines = ["## Variables & Constants\n\n"]

    if constants:
        lines.append("<Cards>\n")
        for const in sorted(constants, key=lambda v: v.name):
            lines.append(f'  <Cards.Card title="{const.name}" href="#constants"/>\n')
        lines.append("</Cards>\n\n")

    if regular_vars:
        lines.append("<Cards>\n")
        for var in sorted(regular_vars, key=lambda v: v.name):
            lines.append(f'  <Cards.Card title="{var.name}" href="#variables"/>\n')
        lines.append("</Cards>\n\n")

    return "".join(lines)


def render_index_cards(
    modules: List[Tuple[str, Optional[str]]], packages: List[Tuple[str, Optional[str]]]
) -> str:
    """
    Render cards for an index page.

    Args:
        modules: List of (module_name, summary) tuples
        packages: List of (package_name, summary) tuples

    Returns:
        Rendered MDX content for index cards
    """
    lines = []

    if packages:
        lines.append("## Packages\n\n")
        lines.append("<Cards>\n")
        for name, summary in sorted(packages):
            lines.append(f'  <Cards.Card title="{name}" href="./{name}"/>\n')
        lines.append("</Cards>\n\n")

    if modules:
        lines.append("## Modules\n\n")
        lines.append("<Cards>\n")
        for name, summary in sorted(modules):
            lines.append(f'  <Cards.Card title="{name}" href="./{name}"/>\n')
        lines.append("</Cards>\n\n")

    return "".join(lines)
