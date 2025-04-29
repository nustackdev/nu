"""
Docstring and module parsing for the Python API Reference Generator.

This module provides functionality to parse Python docstrings and modules
into structured information for documentation generation.
"""

from __future__ import annotations

import inspect
import logging
import re
from typing import Any, Callable, Type, Union

from ..config.models import DiscoveryConfig, RenderingConfig
from ..core.models import (
    ClassAttributeInfo,
    ClassInfo,
    DocstringExample,
    DocstringException,
    DocstringInfo,
    DocstringParameter,
    DocstringReturn,
    FunctionInfo,
    ModuleInfo,
    Signature,
    VariableInfo,
)

logger = logging.getLogger(__name__)


def parse_google_docstring(docstring: str) -> DocstringInfo:  # noqa: C901
    """
    Parse a Google-style docstring into structured components.

    Args:
        docstring: The docstring to parse

    Returns:
        DocstringInfo with parsed docstring components
    """
    if not docstring:
        return DocstringInfo()

    # Clean up the docstring
    docstring = docstring.strip()

    # Initialize result
    result = DocstringInfo()

    # Split into lines for parsing
    lines = docstring.split("\n")

    # Extract summary (first line)
    if lines:
        result.summary = lines[0].strip()
        lines = lines[1:]

    # Process remaining lines
    current_section = "description"
    current_param = None
    current_exception = None
    description_lines = []
    example_lines = []

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines at the beginning
        if not line_stripped and not description_lines and current_section == "description":
            continue

        # Check for section headers
        if re.match(r"^(Args|Parameters|Arguments):", line_stripped, re.I):
            current_section = "parameters"
            continue
        elif re.match(r"^Returns:", line_stripped, re.I):
            current_section = "returns"
            continue
        elif re.match(r"^(Raises|Exceptions):", line_stripped, re.I):
            current_section = "exceptions"
            continue
        elif re.match(r"^Examples?:", line_stripped, re.I):
            current_section = "examples"
            continue
        elif re.match(r"^Attributes:", line_stripped, re.I):
            current_section = "attributes"
            continue

        # Process line based on current section
        if current_section == "description":
            description_lines.append(line)

        elif current_section == "parameters":
            # Check for parameter definition
            param_match = re.match(r"^\s*(\w+)(\s*\(([^)]+)\))?\s*: (.+)$", line_stripped)
            if param_match:
                # New parameter
                param_name = param_match.group(1)
                param_type = param_match.group(3) if param_match.group(2) else None
                param_desc = param_match.group(4).strip()

                # Extract default value if present
                default_value = None
                default_match = re.search(r"Defaults to ([^\.]+)\.", param_desc)
                if default_match:
                    default_value = default_match.group(1).strip()

                current_param = param_name
                result.parameters[param_name] = DocstringParameter(
                    name=param_name,
                    description=param_desc,
                    type_hint=param_type,
                    default=default_value,
                )
            elif current_param and line_stripped:
                # Continuation of the previous parameter description
                result.parameters[current_param].description += " " + line_stripped

                # Check for default value in continuation
                if not result.parameters[current_param].default:
                    default_match = re.search(r"Defaults to ([^\.]+)\.", line_stripped)
                    if default_match:
                        result.parameters[current_param].default = default_match.group(1).strip()

        elif current_section == "returns":
            if not result.returns:
                # Extract type hint if available
                return_type_match = re.match(r"^\s*([^:]+): (.+)$", line_stripped)
                if return_type_match:
                    return_type = return_type_match.group(1).strip()
                    return_desc = return_type_match.group(2).strip()
                    result.returns = DocstringReturn(description=return_desc, type_hint=return_type)
                else:
                    result.returns = DocstringReturn(description=line_stripped)
            elif line_stripped:
                # Continuation of the return description
                result.returns.description += " " + line_stripped

        elif current_section == "exceptions":
            # Check for exception definition
            exception_match = re.match(
                r"^\s*(\w+(?:\.\w+)*(?:\w+)?)(\s*\(.+\))?\s*: (.+)$", line_stripped
            )
            if exception_match:
                # New exception
                exception_name = exception_match.group(1)
                exception_desc = exception_match.group(3).strip()

                current_exception = exception_name
                result.exceptions[exception_name] = DocstringException(
                    name=exception_name, description=exception_desc
                )
            elif current_exception and line_stripped:
                # Continuation of the previous exception description
                result.exceptions[current_exception].description += " " + line_stripped

        elif current_section == "examples":
            # Simplified example handling - just collect lines that start with >>>
            if line_stripped.startswith(">>>") or line_stripped.startswith("..."):
                # Remove the >>> prefix and add to example lines
                example_lines.append(line_stripped[4:])

        elif current_section == "attributes":
            # Check for attribute definition
            attr_match = re.match(r"^\s*(\w+)(\s*\(.+\))?\s*: (.+)$", line_stripped)
            if attr_match:
                # New attribute
                attr_name = attr_match.group(1)
                attr_desc = attr_match.group(3).strip()
                result.attributes[attr_name] = attr_desc
            # No continuation support for attributes

    # If we have example lines, add them as a single example
    if example_lines:
        code = "\n".join(example_lines)
        result.examples.append(DocstringExample(code=code))

    # Combine description lines
    result.description = "\n".join(description_lines).strip()

    return result


class ModuleParser:
    """Parser for Python modules and their components."""

    def __init__(self, config: Union[DiscoveryConfig, RenderingConfig]):
        """
        Initialize the module parser.

        Args:
            config: Configuration for parsing
        """
        self.config = config
        self.show_private = getattr(config, "show_private", False)
        self.show_dunder = getattr(config, "show_dunder", False)
        self.excluded_patterns = getattr(config, "excluded_patterns", [])

    def parse_module(self, module_obj: object, module_name: str) -> ModuleInfo:
        """
        Parse a module into structured information.

        Args:
            module_obj: The module object to parse
            module_name: The name of the module

        Returns:
            ModuleInfo containing structured information about the module
        """
        logger.debug(f"Parsing module: {module_name}")

        # Parse module docstring
        docstring = inspect.getdoc(module_obj)
        docstring_info = parse_google_docstring(docstring) if docstring else None

        # Create module info
        module_info = ModuleInfo(name=module_name, docstring=docstring_info)

        # Parse classes
        for name, obj in inspect.getmembers(module_obj, inspect.isclass):
            # Skip based on configuration
            if not self._should_include_member(name):
                continue

            # Only include classes defined in this module
            if obj.__module__ == module_name:
                try:
                    class_info = self.parse_class(obj, name, module_name)
                    module_info.classes.append(class_info)
                except Exception as e:
                    logger.warning(f"Error parsing class {name} in module {module_name}: {e}")

        # Parse functions
        for name, obj in inspect.getmembers(module_obj, inspect.isfunction):
            # Skip based on configuration
            if not self._should_include_member(name):
                continue

            # Only include functions defined in this module
            if obj.__module__ == module_name:
                try:
                    function_info = self.parse_function(obj, name, module_name)
                    module_info.functions.append(function_info)
                except Exception as e:
                    logger.warning(f"Error parsing function {name} in module {module_name}: {e}")

        # Parse variables
        for name, obj in inspect.getmembers(module_obj):
            # Skip based on configuration
            if not self._should_include_member(name):
                continue

            # Skip modules, classes, and functions
            if (
                inspect.ismodule(obj)
                or inspect.isclass(obj)
                or inspect.isfunction(obj)
                or inspect.isbuiltin(obj)
                or inspect.isroutine(obj)
            ):
                continue

            # Add to variables
            try:
                variable_info = self.parse_variable(name, obj, module_obj)
                module_info.variables.append(variable_info)
            except Exception as e:
                logger.warning(f"Error parsing variable {name} in module {module_name}: {e}")

        return module_info

    def parse_class(self, cls: Type, name: str, module_name: str) -> ClassInfo:  # noqa: C901
        """
        Parse a class into structured information.

        Args:
            cls: The class object to parse
            name: The name of the class
            module_name: The name of the module

        Returns:
            ClassInfo containing structured information about the class
        """
        logger.debug(f"Parsing class: {name}")

        # Parse class docstring
        docstring = inspect.getdoc(cls)
        docstring_info = parse_google_docstring(docstring) if docstring else None

        # Get base classes
        bases = []
        for base in cls.__bases__:
            if base != object:  # Skip 'object' base class
                bases.append(base.__name__)

        # Create class info
        class_info = ClassInfo(name=name, module=module_name, bases=bases, docstring=docstring_info)

        # Parse methods
        for method_name, method_obj in inspect.getmembers(
            cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x)
        ):
            # Skip based on configuration
            if not self._should_include_member(method_name):
                continue

            # Parse the method
            try:
                function_info = self.parse_function(
                    method_obj, method_name, module_name, is_method=True
                )

                # Check if it's a static or class method
                if isinstance(cls.__dict__.get(method_name, None), staticmethod):
                    function_info.is_static = True
                elif isinstance(cls.__dict__.get(method_name, None), classmethod):
                    function_info.is_class_method = True

                class_info.methods.append(function_info)
            except Exception as e:
                logger.warning(f"Error parsing method {method_name} in class {name}: {e}")

        # Parse properties
        for prop_name, prop_obj in inspect.getmembers(cls, lambda x: isinstance(x, property)):
            # Skip based on configuration
            if not self._should_include_member(prop_name):
                continue

            # Parse property getter
            if prop_obj.fget:
                try:
                    function_info = self.parse_function(
                        prop_obj.fget, prop_name, module_name, is_method=True
                    )
                    function_info.is_property = True
                    class_info.properties.append(function_info)
                except Exception as e:
                    logger.warning(f"Error parsing property {prop_name} in class {name}: {e}")

        # Parse class attributes
        for attr_name, attr_value in cls.__dict__.items():
            # Skip methods, properties, and internal attributes
            if (attr_name.startswith("__") and attr_name.endswith("__")) or callable(attr_value):
                continue

            # Skip based on configuration
            if not self._should_include_member(attr_name):
                continue

            # Add to attributes
            try:
                attr_info = ClassAttributeInfo(
                    name=attr_name, value=attr_value, type_name=type(attr_value).__name__
                )
                class_info.attributes.append(attr_info)
            except Exception as e:
                logger.warning(f"Error parsing attribute {attr_name} in class {name}: {e}")

        return class_info

    def parse_function(
        self, func: Callable, name: str, module_name: str, is_method: bool = False
    ) -> FunctionInfo:
        """
        Parse a function into structured information.

        Args:
            func: The function object to parse
            name: The name of the function
            module_name: The name of the module
            is_method: Whether the function is a method

        Returns:
            FunctionInfo containing structured information about the function
        """
        logger.debug(f"Parsing {'method' if is_method else 'function'}: {name}")

        # Parse function docstring
        docstring = inspect.getdoc(func)
        docstring_info = parse_google_docstring(docstring) if docstring else None

        # Get function signature
        try:
            signature_obj = inspect.signature(func)
            signature_str = str(signature_obj)

            # Create signature info
            parameters = []
            for param_name, param in signature_obj.parameters.items():
                # Skip 'self' for instance methods
                if is_method and param_name == "self" and not parameters:
                    continue

                param_info = {
                    "name": param_name,
                    "kind": str(param.kind),
                    "has_default": param.default is not param.empty,
                    "default": None if param.default is param.empty else repr(param.default),
                    "annotation": (
                        None if param.annotation is param.empty else str(param.annotation)
                    ),
                }
                parameters.append(param_info)

            # Extract return type
            return_type = None
            if signature_obj.return_annotation is not signature_obj.empty:
                return_type = str(signature_obj.return_annotation)

            signature = Signature(raw=signature_str, parameters=parameters, return_type=return_type)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error getting signature for {name}: {e}")
            signature = Signature(raw="(...)")

        # Create function info
        function_info = FunctionInfo(
            name=name,
            module=module_name,
            signature=signature,
            docstring=docstring_info,
            is_method=is_method,
        )

        return function_info

    def parse_variable(self, name: str, value: Any, module_obj: object) -> VariableInfo:
        """
        Parse a variable into structured information.

        Args:
            name: The name of the variable
            value: The value of the variable
            module_obj: The module object

        Returns:
            VariableInfo containing structured information about the variable
        """
        # Determine if it's a constant (by convention)
        is_constant = name.isupper()

        # Try to get type name
        type_name = type(value).__name__

        # Try to get docstring from module docstring
        docstring = None
        if module_obj.__doc__:
            # Look for variable documentation in the module docstring
            module_lines = module_obj.__doc__.split("\n")
            for i, line in enumerate(module_lines):
                if f"{name}:" in line or f"{name} -" in line or f"{name} –" in line:
                    parts = line.split(":", 1) if ":" in line else line.split("-", 1)
                    if len(parts) > 1:
                        docstring = parts[1].strip()

                        # Check for multi-line description
                        for j in range(i + 1, len(module_lines)):
                            next_line = module_lines[j].strip()
                            if not next_line or next_line.startswith(
                                tuple(
                                    string + ":"
                                    for string in ["Args", "Returns", "Raises", "Example"]
                                )
                            ):
                                break
                            if not next_line.startswith(
                                tuple(
                                    string + ":"
                                    for string in ["Args", "Returns", "Raises", "Example"]
                                )
                            ):
                                docstring += " " + next_line
                        break

        # Create variable info
        return VariableInfo(
            name=name,
            value=value,
            type_name=type_name,
            is_constant=is_constant,
            docstring=docstring,
        )

    def _should_include_member(self, name: str) -> bool:
        """
        Determine if a member should be included based on configuration.

        Args:
            name: Name of the member

        Returns:
            True if the member should be included, False otherwise
        """
        # Check exclusion patterns
        for pattern in self.excluded_patterns:
            if re.match(pattern, name):
                return False

        if name.startswith("_"):
            # Check dunder methods inclision
            if name.startswith("__") and name.endswith("__"):
                return self.show_dunder

            # Check private member inclusion
            return self.show_private

        return True
