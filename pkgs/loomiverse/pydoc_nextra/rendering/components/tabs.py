"""
Tabs component rendering for the Python API Reference Generator.

This module provides functionality to render Nextra tabs components.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")


def render_tabs(
    items: List[T],
    item_title_fn: Callable[[T], str],
    item_content_fn: Callable[[T], str],
    sort_key: Optional[Callable[[T], Any]] = None,
) -> str:
    """
    Render a collection of items as tabs.

    Args:
        items: List of items to render as tabs
        item_title_fn: Function to extract tab title from item
        item_content_fn: Function to render tab content from item
        sort_key: Optional function for sorting items

    Returns:
        Rendered MDX content for tabs
    """
    if not items:
        return ""

    # Sort items if sort key provided
    if sort_key:
        sorted_items = sorted(items, key=sort_key)
    else:
        sorted_items = items

    # Extract item titles
    item_titles = [f"'{item_title_fn(item)}'" for item in sorted_items]

    lines = ["<Tabs items={[" + ", ".join(item_titles) + "]}>\n"]

    # Render each tab
    for item in sorted_items:
        lines.append("<Tabs.Tab>\n\n")
        lines.append(item_content_fn(item))
        lines.append("</Tabs.Tab>\n\n")

    lines.append("</Tabs>\n\n")

    return "".join(lines)


def render_method_tabs(methods: List[Any], method_renderer: Callable[[Any], str]) -> str:
    """
    Render class methods as tabs.

    Args:
        methods: List of method info objects
        method_renderer: Function to render a method

    Returns:
        Rendered MDX content for method tabs
    """
    if not methods:
        return ""

    # If few methods, don't use tabs
    if len(methods) <= 3:
        return "".join(
            [method_renderer(method) for method in sorted(methods, key=lambda m: m.name)]
        )

    # Use tabs for many methods
    return render_tabs(
        items=methods,
        item_title_fn=lambda m: m.name,
        item_content_fn=method_renderer,
        sort_key=lambda m: m.name,
    )


def render_examples_tabs(examples: List[str]) -> str:
    """
    Render examples as tabs.

    Args:
        examples: List of example code snippets

    Returns:
        Rendered MDX content for example tabs
    """
    if not examples:
        return ""

    # If only one example, don't use tabs
    if len(examples) == 1:
        return f"```python filename='example.py'\n{examples[0].strip()}\n```\n\n"

    # Use tabs for multiple examples
    lines = [
        "<Tabs items={[" + ", ".join([f"'Example {i + 1}'" for i in range(len(examples))]) + "]}>\n"
    ]

    for i, example in enumerate(examples):
        lines.append("<Tabs.Tab>\n\n")
        lines.append(f"```python filename='example_{i + 1}.py'\n{example.strip()}\n```\n\n")
        lines.append("</Tabs.Tab>\n\n")

    lines.append("</Tabs>\n\n")

    return "".join(lines)
