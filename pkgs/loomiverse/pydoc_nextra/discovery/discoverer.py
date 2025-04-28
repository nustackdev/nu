"""
Module discovery for the Python API Reference Generator.

This module provides functionality to discover Python modules based on
configuration settings.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
import re
import sys
from typing import Dict, Optional

from ..config.models import DiscoveryConfig, ModuleConfig, RenderingConfig
from ..core.models import ModuleInfo
from .parser import ModuleParser

logger = logging.getLogger(__name__)


class ModuleDiscoverer:
    """Discovers Python modules based on configuration."""

    def __init__(self, config: DiscoveryConfig):
        """
        Initialize the module discoverer.

        Args:
            config: Configuration for module discovery
        """
        self.config = config
        self.discovered_modules: Dict[str, object] = {}
        self.module_parser = ModuleParser(config)

    def discover_modules(self) -> Dict[str, object]:
        """
        Discover Python modules based on configuration.

        Returns:
            Dictionary mapping module names to module objects
        """
        logger.info(f"Discovering modules in {self.config.source_dir}")

        # Add source directory to sys.path temporarily to allow imports
        source_dir_str = str(self.config.source_dir.resolve())
        sys.path.insert(0, source_dir_str)

        try:
            modules = {}

            # If specific modules are specified in config, use those
            if self.config.modules:
                for module_config in self.config.modules:
                    self._discover_specific_module(module_config, modules)
            else:
                # Otherwise discover all modules in source directory
                self._discover_all_modules(modules)

            # Store discovered modules
            self.discovered_modules = modules
            logger.info(f"Discovered {len(modules)} modules")

            return modules

        finally:
            # Clean up sys.path
            if source_dir_str in sys.path:
                sys.path.remove(source_dir_str)

    def _discover_specific_module(
        self, module_config: ModuleConfig, modules: Dict[str, object]
    ) -> None:
        """
        Discover a specific module based on its configuration.

        Args:
            module_config: Configuration for the module
            modules: Dictionary to store discovered modules
        """
        try:
            if "*" in module_config.name:
                # Handle wildcard patterns
                pattern = module_config.name.replace("*", "")
                for finder, name, is_pkg in pkgutil.iter_modules([str(self.config.source_dir)]):
                    if pattern in name and name not in self.config.exclude_modules:
                        try:
                            module = importlib.import_module(name)
                            modules[name] = module
                            logger.debug(f"Discovered module: {name}")
                        except ImportError as e:
                            logger.warning(f"Failed to import module {name}: {e}")
            else:
                # Direct module import
                name = module_config.name
                if name not in self.config.exclude_modules:
                    try:
                        module = importlib.import_module(name)
                        modules[name] = module
                        logger.debug(f"Discovered module: {name}")

                        # Discover submodules if it's a package and recursive discovery is enabled
                        if self.config.recursive and hasattr(module, "__path__"):
                            self._discover_package_modules(module, modules)
                    except ImportError as e:
                        logger.warning(f"Failed to import module {name}: {e}")
        except Exception as e:
            logger.error(f"Error discovering module {module_config.name}: {e}")

    def _discover_all_modules(self, modules: Dict[str, object]) -> None:
        """
        Discover all modules in the source directory.

        Args:
            modules: Dictionary to store discovered modules
        """
        source_dir = str(self.config.source_dir)

        for finder, name, is_pkg in pkgutil.iter_modules([source_dir]):
            # Check if the module should be excluded
            if name in self.config.exclude_modules:
                continue

            # Check exclusion patterns
            excluded = False
            for pattern in self.config.exclude_patterns:
                if re.match(re.compile(pattern, re.IGNORECASE), name):
                    excluded = True
                    break

            if excluded:
                continue

            # Import the module
            try:
                module = importlib.import_module(name)
                modules[name] = module
                logger.debug(f"Discovered module: {name}")

                # Discover submodules if it's a package and recursive discovery is enabled
                if self.config.recursive and is_pkg:
                    self._discover_package_modules(module, modules)
            except ImportError as e:
                logger.warning(f"Failed to import module {name}: {e}")

    def _discover_package_modules(self, package: object, modules: Dict[str, object]) -> None:
        """
        Discover submodules of a package.

        Args:
            package: The package module object
            modules: Dictionary to store discovered modules
        """
        if not hasattr(package, "__path__"):
            return

        package_path = getattr(package, "__path__", [])
        package_name = getattr(package, "__name__", "")

        for finder, name, is_pkg in pkgutil.iter_modules(package_path):
            full_name = f"{package_name}.{name}"

            # Skip if in exclude list
            if full_name in self.config.exclude_modules:
                continue

            # Check exclusion patterns
            excluded = False
            for pattern in self.config.exclude_patterns:
                if re.match(re.compile(pattern, re.IGNORECASE), name):
                    excluded = True
                    break

            if excluded:
                continue

            # Import the submodule
            try:
                module = importlib.import_module(full_name)
                modules[full_name] = module
                logger.debug(f"Discovered submodule: {full_name}")

                # Recursively discover submodules
                if self.config.recursive and is_pkg:
                    self._discover_package_modules(module, modules)
            except ImportError as e:
                logger.warning(f"Failed to import submodule {full_name}: {e}")

    def parse_modules(self) -> Dict[str, ModuleInfo]:
        """
        Parse all discovered modules.

        Returns:
            Dictionary mapping module names to parsed module information
        """
        if not self.discovered_modules:
            logger.warning("No modules discovered to parse")
            return {}

        parsed_modules = {}

        for module_name, module_obj in self.discovered_modules.items():
            try:
                # Set module-specific parser configuration if available
                module_config = self._get_module_config(module_name)
                if module_config:
                    # Create a temporary RenderingConfig from ModuleConfig
                    # This fixes the type error by creating a compatible config object
                    temp_config = RenderingConfig(
                        show_private=module_config.include_private,
                        show_dunder=module_config.include_dunder,
                        excluded_patterns=module_config.exclude_patterns,
                    )
                    parser = ModuleParser(temp_config)
                else:
                    parser = self.module_parser

                # Parse the module
                module_info = parser.parse_module(module_obj, module_name)

                # Add submodules (discovered modules that are submodules of this one)
                for submodule_name in self.discovered_modules.keys():
                    if (
                        submodule_name.startswith(module_name + ".")
                        and "." not in submodule_name[len(module_name) + 1 :]
                    ):
                        module_info.submodules.append(submodule_name)

                parsed_modules[module_name] = module_info
                logger.debug(f"Parsed module: {module_name}")
            except Exception as e:
                logger.error(f"Error parsing module {module_name}: {e}")

        logger.info(f"Parsed {len(parsed_modules)} modules")
        return parsed_modules

    def _get_module_config(self, module_name: str) -> Optional[ModuleConfig]:
        """
        Get module-specific configuration if available.

        Args:
            module_name: Name of the module

        Returns:
            ModuleConfig for the module or None if not found
        """
        for module_config in self.config.modules:
            if module_config.name == module_name:
                return module_config

            # Check for wildcard matches
            if "*" in module_config.name:
                pattern = module_config.name.replace("*", "")
                if module_name.startswith(pattern):
                    return module_config

        return None
