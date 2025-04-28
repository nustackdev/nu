"""
Core domain models for the Python API Reference Generator.

This module contains data classes representing the structure of Python modules,
classes, functions, and docstrings for documentation generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class DocstringParameter:
    """Information about a parameter in a docstring."""

    name: str
    description: str = ""
    type_hint: Optional[str] = None
    default: Optional[str] = None


@dataclass
class DocstringReturn:
    """Information about a return value in a docstring."""

    description: str = ""
    type_hint: Optional[str] = None


@dataclass
class DocstringException:
    """Information about an exception in a docstring."""

    name: str
    description: str = ""


@dataclass
class DocstringExample:
    """Code example from a docstring."""

    code: str
    description: Optional[str] = None


@dataclass
class DocstringInfo:
    """Structured information parsed from a docstring."""

    summary: str = ""
    description: str = ""
    parameters: Dict[str, DocstringParameter] = field(default_factory=dict)
    returns: Optional[DocstringReturn] = None
    exceptions: Dict[str, DocstringException] = field(default_factory=dict)
    examples: List[DocstringExample] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)

    def has_content(self) -> bool:
        """Check if the docstring has any content at all."""
        return bool(
            self.summary
            or self.description
            or self.parameters
            or self.returns
            or self.exceptions
            or self.examples
            or self.attributes
        )


@dataclass
class Signature:
    """Information about a callable's signature."""

    raw: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None

    @classmethod
    def from_string(cls, signature_str: str) -> Signature:
        """Create a Signature from a string representation."""
        return cls(raw=signature_str)


@dataclass
class FunctionInfo:
    """Information about a Python function or method."""

    name: str
    module: str
    signature: Signature
    docstring: Optional[DocstringInfo] = None
    is_method: bool = False
    is_property: bool = False
    is_static: bool = False
    is_class_method: bool = False

    @classmethod
    def create(cls, name: str, module: str, signature_str: str = "()") -> FunctionInfo:
        """Create a FunctionInfo with minimal information."""
        return cls(name=name, module=module, signature=Signature.from_string(signature_str))


@dataclass
class ClassAttributeInfo:
    """Information about a class attribute."""

    name: str
    value: Any
    type_name: str = ""
    docstring: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a Python class."""

    name: str
    module: str
    bases: List[str] = field(default_factory=list)
    docstring: Optional[DocstringInfo] = None
    methods: List[FunctionInfo] = field(default_factory=list)
    properties: List[FunctionInfo] = field(default_factory=list)
    attributes: List[ClassAttributeInfo] = field(default_factory=list)


@dataclass
class VariableInfo:
    """Information about a Python variable or constant."""

    name: str
    value: Any
    type_name: str
    is_constant: bool = False
    docstring: Optional[str] = None


@dataclass
class ModuleInfo:
    """Information about a Python module."""

    name: str
    docstring: Optional[DocstringInfo] = None
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    variables: List[VariableInfo] = field(default_factory=list)
    submodules: List[str] = field(default_factory=list)

    def get_class_by_name(self, name: str) -> Optional[ClassInfo]:
        """Get a class by name."""
        for cls in self.classes:
            if cls.name == name:
                return cls
        return None

    def get_function_by_name(self, name: str) -> Optional[FunctionInfo]:
        """Get a function by name."""
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def get_variable_by_name(self, name: str) -> Optional[VariableInfo]:
        """Get a variable by name."""
        for var in self.variables:
            if var.name == name:
                return var
        return None
