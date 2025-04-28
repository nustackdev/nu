"""
Configuration module for the Python API Reference Generator.

This module provides configuration models and loading utilities.
"""

from .loader import load_config_from_dict, load_config_from_file
from .models import Configuration, DiscoveryConfig, ModuleConfig, OutputConfig, RenderingConfig

__all__ = [
    "Configuration",
    "DiscoveryConfig",
    "RenderingConfig",
    "OutputConfig",
    "ModuleConfig",
    "load_config_from_file",
    "load_config_from_dict",
]
