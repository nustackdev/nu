"""
Configuration models for the Python API Reference Generator.

This module defines the configuration structure for the generator,
including discovery patterns, output paths, and formatting options.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ModuleConfig:
    """Configuration for a specific module."""

    name: str
    """Module name or pattern to match."""

    title: Optional[str] = None
    """Override title for the module in documentation."""

    show_private: bool = False
    """Whether to include private members (prefixed with _)."""

    show_dunder: bool = False
    """Whether to include dunder methods (__method__)."""

    exclude_patterns: List[str] = field(default_factory=list)
    """Patterns of members to exclude."""


@dataclass
class DiscoveryConfig:
    """Configuration for module discovery."""

    source_dir: Path
    """Directory containing the Python modules to document."""

    modules: List[ModuleConfig] = field(default_factory=list)
    """Specific modules to document and their configuration."""

    exclude_modules: List[str] = field(default_factory=list)
    """Modules to exclude from documentation."""

    exclude_patterns: List[str] = field(default_factory=list)
    """Patterns of modules to exclude."""

    recursive: bool = True
    """Whether to recursively discover modules in subdirectories."""


@dataclass
class RenderingConfig:
    """Configuration for document rendering."""

    show_private: bool = False
    """Whether to show private members (prefixed with _)."""

    show_dunder: bool = False
    """Whether to show dunder methods (__method__)."""

    excluded_patterns: List[str] = field(default_factory=list)
    """Patterns of members to exclude."""

    section_order: List[str] = field(
        default_factory=lambda: ["Classes", "Functions", "Variables", "Modules"]
    )
    """Order of sections in the documentation."""

    include_source_code: bool = False
    """Whether to include the source code in the documentation."""

    emojis: Dict[str, str] = field(
        default_factory=lambda: {
            "module": "📦",
            "class": "🧩",
            "function": "⚙️",
            "method": "🔧",
            "property": "🔑",
            "attribute": "📄",
            "variable": "🔢",
            "constant": "🔒",
        }
    )
    """Emoji mapping for different types."""


@dataclass
class OutputConfig:
    """Configuration for output management."""

    output_dir: Path
    """Directory where MDX files will be generated."""

    meta_filename: str = "_meta.json"
    """Filename for the metadata file (used by Nextra for navigation)."""

    create_index: bool = True
    """Whether to create index.mdx files for directories."""

    overwrite: bool = True
    """Whether to overwrite existing files."""


@dataclass
class Configuration:
    """Main configuration for the documentation generator."""

    discovery: DiscoveryConfig
    """Configuration for module discovery."""

    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    """Configuration for document rendering."""

    output: OutputConfig = field(default_factory=lambda: OutputConfig(output_dir=Path("./docs")))
    """Configuration for output management."""

    @classmethod
    def create(
        cls, source_dir: Union[str, Path], output_dir: Union[str, Path], **kwargs: Any
    ) -> Configuration:
        """
        Create a Configuration with minimal parameters.

        Args:
            source_dir: Directory containing the Python modules to document
            output_dir: Directory where MDX files will be generated
            **kwargs: Additional configuration options

        Returns:
            Configuration instance
        """
        source_path = Path(source_dir) if isinstance(source_dir, str) else source_dir
        output_path = Path(output_dir) if isinstance(output_dir, str) else output_dir

        # Extract configuration for different sections
        discovery_kwargs = {}
        rendering_kwargs = {}
        output_kwargs = {}

        # Handle modules list specially
        modules_list = kwargs.pop("modules", [])
        modules = []
        for item in modules_list:
            if isinstance(item, dict):
                modules.append(ModuleConfig(**item))
            elif isinstance(item, str):
                modules.append(ModuleConfig(name=item))
            elif isinstance(item, ModuleConfig):
                modules.append(item)

        discovery_kwargs["modules"] = modules

        # Process remaining kwargs
        for key, value in kwargs.items():
            if hasattr(DiscoveryConfig, key):
                discovery_kwargs[key] = value
            elif hasattr(RenderingConfig, key):
                rendering_kwargs[key] = value
            elif hasattr(OutputConfig, key):
                output_kwargs[key] = value

        # Create config objects
        discovery_config = DiscoveryConfig(source_dir=source_path, **discovery_kwargs)
        rendering_config = RenderingConfig(**rendering_kwargs)
        output_config = OutputConfig(output_dir=output_path, **output_kwargs)

        return cls(discovery=discovery_config, rendering=rendering_config, output=output_config)
