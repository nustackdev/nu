"""
Code block rendering for the Python API Reference Generator.

This module provides functionality to render code blocks with enhanced features.
"""

from __future__ import annotations

import inspect
from typing import Any, List

from ...core.models import FunctionInfo, Signature


def render_signature(
    name: str, signature: Signature, qualifier: str = "", filename: str = "function.py"
) -> str:
    """
    Render a Python function or method signature as a code block.

    Args:
        name: Function or method name
        signature: Signature information
        qualifier: Optional decorators or qualifiers (e.g., @staticmethod)
        filename: Filename to display in the code block

    Returns:
        Rendered MDX code block with the signature
    """
    if qualifier:
        qualifier = qualifier.strip() + "\n"

    return f"```python filename='{filename}'\n{qualifier}def {name}{signature.raw}\n```\n\n"


def render_function_signature(function_info: FunctionInfo) -> str:
    """
    Render a function signature as a code block.

    Args:
        function_info: Function information

    Returns:
        Rendered MDX code block with the function signature
    """
    return render_signature(
        name=function_info.name, signature=function_info.signature, filename="function.py"
    )


def render_method_signature(method_info: FunctionInfo) -> str:
    """
    Render a method signature as a code block.

    Args:
        method_info: Method information

    Returns:
        Rendered MDX code block with the method signature
    """
    qualifier = ""
    if method_info.is_static:
        qualifier = "@staticmethod"
    elif method_info.is_class_method:
        qualifier = "@classmethod"
    elif method_info.is_property:
        qualifier = "@property"

    # Convert signature to include self if needed
    signature = method_info.signature
    if (
        method_info.is_method
        and not method_info.is_static
        and signature.raw.startswith("(")
        and "self" not in signature.raw.split(",")[0]
    ):
        # Add self parameter if it's missing
        raw_sig = signature.raw
        sig = f"(self{raw_sig[1:]}"
        signature = Signature(
            raw=sig, parameters=signature.parameters, return_type=signature.return_type
        )

    return render_signature(
        name=method_info.name, signature=signature, qualifier=qualifier, filename="method.py"
    )


def render_class_definition(
    name: str, bases: List[str] | None = None, filename: str = "class.py"
) -> str:
    """
    Render a Python class definition as a code block.

    Args:
        name: Class name
        bases: Base classes
        filename: Filename to display in the code block

    Returns:
        Rendered MDX code block with the class definition
    """
    if not bases:
        bases = []

    if bases:
        bases_str = "(" + ", ".join(bases) + ")"
    else:
        bases_str = ""

    return f"```python filename='{filename}'\nclass {name}{bases_str}:\n    ...\n```\n\n"


def render_example(example: str, index: int) -> str:
    """
    Render an example code snippet.

    Args:
        example: Example code
        index: Example index

    Returns:
        Rendered MDX code block for the example
    """
    return f"```python filename='example_{index}.py'\n{example.strip()}\n```\n\n"


def render_source_code(obj: Any) -> str:
    """
    Render the source code of an object if available.

    Args:
        obj: Object to get source code from

    Returns:
        Rendered MDX code block with the source code
    """
    try:
        source = inspect.getsource(obj)
        return f"```python filename='source.py'\n{source}\n```\n\n"
    except (TypeError, OSError, IOError):
        return "```python\n# Source code not available\n```\n\n"


def enhance_code_blocks(content: str) -> str:
    """
    Enhance code blocks with line highlighting and other features.

    Args:
        content: MDX content to process

    Returns:
        Enhanced MDX content
    """
    import re

    # Find code blocks
    code_block_pattern = r"```(\w+)(?:\s+(.+?))?\n(.*?)```"
    matches = re.finditer(code_block_pattern, content, re.DOTALL)
    replacements = []

    for match in matches:
        lang = match.group(1)
        options = match.group(2) or ""
        code = match.group(3)

        # Look for highlight comments in the code
        highlight_lines = []
        filename = None

        # Check for highlight comments
        for i, line in enumerate(code.split("\n"), 1):
            if "# highlight-line" in line:
                highlight_lines.append(str(i))

            # Check for filename comment
            filename_match = re.search(r"# filename: ([\w\.\-/]+)", line)
            if filename_match:
                filename = filename_match.group(1)

        # Build new options
        new_options = []
        if options:
            new_options.append(options)

        if highlight_lines:
            new_options.append(f"{{{{ {','.join(highlight_lines)} }}}}")

        if filename:
            new_options.append(f'filename="{filename}"')

        # Assemble new code block
        new_code_block = f"```{lang}"
        if new_options:
            new_code_block += " " + " ".join(new_options)
        new_code_block += f"\n{code}```"

        replacements.append((match.group(0), new_code_block))

    # Apply replacements
    for old, new in reversed(replacements):
        content = content.replace(old, new)

    return content
