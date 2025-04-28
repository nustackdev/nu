"""
Main generator for the Python API Reference Generator.

This module provides the main generator class that orchestrates the
discovery, parsing, rendering, and output of Python API documentation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from .config.models import Configuration
from .core.models import ModuleInfo
from .discovery import ModuleDiscoverer
from .output import OutputManager
from .rendering import MDXRenderer

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Main class for generating MDX documentation from Python modules."""

    def __init__(self, config: Configuration):
        """
        Initialize the documentation generator.

        Args:
            config: Optional configuration
        """
        self.config = config
        self._discoverer = None
        self._discovered_modules: Dict[str, object] = {}
        self._parsed_modules: Dict[str, ModuleInfo] = {}

    def set_config(self, config: Configuration) -> None:
        """
        Set the configuration for the generator.

        Args:
            config: Configuration object
        """
        self.config = config
        logger.info(
            f"Configuration set: source_dir={config.discovery.source_dir}, output_dir={config.output.output_dir}"
        )

    def discover_modules(self) -> Dict[str, object]:
        """
        Discover modules based on configuration.

        Returns:
            Dictionary mapping module names to module objects

        Raises:
            ValueError: If configuration has not been set
        """
        if not self.config:
            raise ValueError("Configuration not set. Call set_config() first.")

        # Create module discoverer
        self._discoverer = ModuleDiscoverer(self.config.discovery)

        # Discover modules
        self._discovered_modules = self._discoverer.discover_modules()

        return self._discovered_modules

    def parse_modules(self) -> Dict[str, ModuleInfo]:
        """
        Parse discovered modules.

        Returns:
            Dictionary mapping module names to parsed module information

        Raises:
            ValueError: If no modules have been discovered
        """
        if not self._discovered_modules:
            raise ValueError("No modules discovered. Call discover_modules() first.")

        if not self._discoverer:
            raise ValueError("Module discoverer not initialized. Call discover_modules() first.")

        # Use the existing discoverer that already has the discovered modules
        self._parsed_modules = self._discoverer.parse_modules()

        return self._parsed_modules

    def render_modules(self) -> Dict[str, str]:
        """
        Render parsed modules to MDX.

        Returns:
            Dictionary mapping module names to MDX content

        Raises:
            ValueError: If no modules have been parsed
        """
        if not self._parsed_modules:
            raise ValueError("No modules parsed. Call parse_modules() first.")

        # Create renderer
        renderer = MDXRenderer(self.config.rendering)

        # Render modules
        rendered_modules = {}
        for module_name, module_info in self._parsed_modules.items():
            try:
                mdx_content = renderer.render_module(module_info)
                rendered_modules[module_name] = mdx_content
                logger.debug(f"Rendered module: {module_name}")
            except Exception as e:
                logger.error(f"Error rendering module {module_name}: {e}")

        logger.info(f"Rendered {len(rendered_modules)} modules")
        return rendered_modules

    def write_modules(self, rendered_modules: Dict[str, str]) -> List[Path]:
        """
        Write rendered modules to files.

        Args:
            rendered_modules: Dictionary mapping module names to MDX content

        Returns:
            List of paths to written files
        """
        # Create output manager
        output_manager = OutputManager(self.config.output)

        # Write modules
        written_files = []
        for module_name, mdx_content in rendered_modules.items():
            try:
                output_file = output_manager.write_module_doc(module_name, mdx_content)
                written_files.append(output_file)
            except Exception as e:
                logger.error(f"Error writing module {module_name}: {e}")

        # Generate navigation
        try:
            output_manager.generate_navigation(self._discovered_modules, self._parsed_modules)
        except Exception as e:
            logger.error(f"Error generating navigation: {e}")

        return written_files

    def generate(self) -> List[Path]:
        """
        Generate documentation for all modules.

        Returns:
            List of paths to generated files

        Raises:
            ValueError: If configuration has not been set
        """
        if not self.config:
            raise ValueError("Configuration not set. Call set_config() first.")

        logger.info("Starting documentation generation")

        # Step 1: Discover modules
        logger.info("Discovering modules...")
        self.discover_modules()
        logger.info(f"Discovered {len(self._discovered_modules)} modules")

        # Step 2: Parse modules
        logger.info("Parsing modules...")
        self.parse_modules()
        logger.info(f"Parsed {len(self._parsed_modules)} modules")

        # Step 3: Render modules
        logger.info("Rendering modules...")
        rendered_modules = self.render_modules()
        logger.info(f"Rendered {len(rendered_modules)} modules")

        # Step 4: Write modules and generate navigation
        logger.info("Writing files and generating navigation...")
        written_files = self.write_modules(rendered_modules)
        logger.info(f"Written {len(written_files)} files")

        logger.info("Documentation generation complete")
        return written_files
