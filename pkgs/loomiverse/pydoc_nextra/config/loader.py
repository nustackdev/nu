"""
Configuration loading utilities for the Python API Reference Generator.

This module provides functionality to load configurations from files or dictionaries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .models import Configuration, DiscoveryConfig, ModuleConfig, OutputConfig, RenderingConfig


def load_config_from_file(file_path: Union[str, Path]) -> Configuration:
    """
    Load configuration from a JSON or YAML file.

    Args:
        file_path: Path to the configuration file

    Returns:
        Configuration instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported
        ImportError: If PyYAML is required but not installed
    """
    path = Path(file_path) if isinstance(file_path, str) else file_path

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
    elif path.suffix.lower() in (".yml", ".yaml"):
        try:
            import yaml

            with open(path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        except ImportError:
            raise ImportError("PyYAML is required to load YAML configuration files")
    else:
        raise ValueError(f"Unsupported configuration file format: {path.suffix}")

    return load_config_from_dict(config_dict)


def load_config_from_dict(config_dict: Dict[str, Any]) -> Configuration:
    """
    Load configuration from a dictionary.

    Args:
        config_dict: Dictionary with configuration values

    Returns:
        Configuration instance
    """
    # Extract source_dir and output_dir (required)
    source_dir = config_dict.get("discovery", {}).get("source_dir")
    if not source_dir:
        raise ValueError("source_dir is required in configuration")

    output_dir = config_dict.get("output", {}).get("output_dir")
    if not output_dir:
        raise ValueError("output_dir is required in configuration")

    # Handle discovery config
    discovery_dict = config_dict.get("discovery", {})
    if not discovery_dict:
        # If no discovery section, use top-level keys that match DiscoveryConfig
        discovery_dict = {
            "source_dir": source_dir,
            "modules": config_dict.get("modules", []),
            "exclude_modules": config_dict.get("exclude_modules", []),
            "exclude_patterns": config_dict.get("exclude_patterns", []),
            "recursive": config_dict.get("recursive", True),
        }
    else:
        # Ensure source_dir is in discovery config
        discovery_dict["source_dir"] = source_dir

    # Process modules
    modules_list = discovery_dict.get("modules", [])
    modules = []
    for item in modules_list:
        if isinstance(item, dict):
            modules.append(ModuleConfig(**item))
        elif isinstance(item, str):
            modules.append(ModuleConfig(name=item))

    discovery_dict["modules"] = modules

    # Create discovery config
    discovery_config = DiscoveryConfig(
        source_dir=Path(discovery_dict["source_dir"]),
        modules=discovery_dict["modules"],
        exclude_modules=discovery_dict.get("exclude_modules", []),
        exclude_patterns=discovery_dict.get("exclude_patterns", []),
        recursive=discovery_dict.get("recursive", True),
    )

    # Handle rendering config
    rendering_dict = config_dict.get("rendering", {})
    if not rendering_dict:
        # If no rendering section, use top-level keys that match RenderingConfig
        rendering_dict = {
            "show_private": config_dict.get("show_private", False),
            "show_dunder": config_dict.get("show_dunder", False),
            "excluded_patterns": config_dict.get("excluded_patterns", []),
            "section_order": config_dict.get(
                "section_order", ["Classes", "Functions", "Variables", "Modules"]
            ),
            "include_source_code": config_dict.get("include_source_code", False),
            "emojis": config_dict.get("emojis", {}),
        }

    # Handle emojis
    emojis = rendering_dict.get("emojis", {})
    default_emojis = {
        "module": "📦",
        "class": "🧩",
        "function": "⚙️",
        "method": "🔧",
        "property": "🔑",
        "attribute": "📄",
        "variable": "🔢",
        "constant": "🔒",
    }

    # Update default emojis with user-provided ones
    default_emojis.update(emojis)
    rendering_dict["emojis"] = default_emojis

    # Create rendering config
    rendering_config = RenderingConfig(
        show_private=rendering_dict.get("show_private", False),
        show_dunder=rendering_dict.get("show_dunder", False),
        excluded_patterns=rendering_dict.get("excluded_patterns", []),
        section_order=rendering_dict.get(
            "section_order", ["Classes", "Functions", "Variables", "Modules"]
        ),
        include_source_code=rendering_dict.get("include_source_code", False),
        emojis=rendering_dict["emojis"],
    )

    # Handle output config
    output_dict = config_dict.get("output", {})
    if not output_dict:
        # If no output section, use top-level keys that match OutputConfig
        output_dict = {
            "output_dir": output_dir,
            "meta_filename": config_dict.get("meta_filename", "_meta.json"),
            "create_index": config_dict.get("create_index", True),
            "overwrite": config_dict.get("overwrite", True),
        }
    else:
        # Ensure output_dir is in output config
        output_dict["output_dir"] = output_dir

    # Create output config
    output_config = OutputConfig(
        output_dir=Path(output_dict["output_dir"]),
        meta_filename=output_dict.get("meta_filename", "_meta.json"),
        create_index=output_dict.get("create_index", True),
        overwrite=output_dict.get("overwrite", True),
    )

    # Create final configuration
    return Configuration(
        discovery=discovery_config, rendering=rendering_config, output=output_config
    )
