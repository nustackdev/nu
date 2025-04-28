"""
Discovery module for the Python API Reference Generator.

This module provides functionality to discover and parse Python modules.
"""

from .discoverer import ModuleDiscoverer
from .parser import ModuleParser, parse_google_docstring

__all__ = ["ModuleDiscoverer", "ModuleParser", "parse_google_docstring"]
