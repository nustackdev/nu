"""
Callout component rendering for the Python API Reference Generator.

This module provides functionality to render Nextra callout components.
"""

from __future__ import annotations

from typing import Literal, Optional

from ...core.models import ClassInfo, DocstringInfo

CalloutType = Literal["default", "info", "warning", "error"]


def render_summary_callout(summary: str, callout_type: CalloutType = "default") -> str:
    """
    Render a summary in a callout.

    Args:
        summary: Summary text
        callout_type: Type of callout

    Returns:
        Rendered MDX content for callout
    """
    if not summary:
        return ""

    type_attr = f' type="{callout_type}"' if callout_type != "default" else ""

    return f"<Callout{type_attr}>\n{summary}\n</Callout>\n\n"


def render_inheritance_callout(class_info: ClassInfo) -> str:
    """
    Render class inheritance information in a callout.

    Args:
        class_info: Class information

    Returns:
        Rendered MDX content for inheritance callout
    """
    if not class_info.bases:
        return ""

    base_names = [f"`{base}`" for base in class_info.bases]
    inheritance = ", ".join(base_names)

    return f"<Callout type='info'>\n  Inherits from: {inheritance}\n</Callout>\n\n"


def render_deprecation_callout(docstring: Optional[DocstringInfo]) -> str:
    """
    Render deprecation warning in a callout if present in docstring.

    Args:
        docstring: Docstring information

    Returns:
        Rendered MDX content for deprecation callout
    """
    if not docstring or not docstring.description:
        return ""

    # Look for deprecation notices in the description
    desc = docstring.description.lower()
    if "deprecated" in desc or "deprecation" in desc:
        # Try to extract the deprecation message
        import re

        # Look for common deprecation patterns
        patterns = [
            r"(?i)deprecated[\s:]+(.*?)(?:\n\n|$)",
            r"(?i)deprecation warning[\s:]+(.*?)(?:\n\n|$)",
            r"(?i)warning[\s:]+deprecated(.*?)(?:\n\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, docstring.description, re.DOTALL)
            if match:
                message = match.group(1).strip()
                return f"<Callout type='warning'>\n  **Deprecated:** {message}\n</Callout>\n\n"

        # If no specific message found but "deprecated" is present
        return "<Callout type='warning'>\n  **Deprecated:** This feature is deprecated and may be removed in a future version.\n</Callout>\n\n"

    return ""


def render_note_callout(note: str) -> str:
    """
    Render a note in a callout.

    Args:
        note: Note text

    Returns:
        Rendered MDX content for note callout
    """
    if not note:
        return ""

    return f"<Callout type='info'>\n  **Note:** {note}\n</Callout>\n\n"


def render_warning_callout(warning: str) -> str:
    """
    Render a warning in a callout.

    Args:
        warning: Warning text

    Returns:
        Rendered MDX content for warning callout
    """
    if not warning:
        return ""

    return f"<Callout type='warning'>\n  **Warning:** {warning}\n</Callout>\n\n"
