"""
Output management for the Python API Reference Generator.

This module provides functionality to write MDX files and generate
navigation structures.
"""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set

from ..config.models import OutputConfig
from ..core.models import ModuleInfo

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages writing MDX files and navigation structures."""

    def __init__(self, config: OutputConfig):
        """
        Initialize the output manager.

        Args:
            config: Configuration for output
        """
        self.config = config

        # Ensure output directory exists
        os.makedirs(config.output_dir, exist_ok=True)

    def write_module_doc(self, module_name: str, content: str) -> Path:
        """
        Write a module document to the file system.

        Args:
            module_name: Name of the module
            content: MDX content to write

        Returns:
            Path to the written file
        """
        # Convert module name to path
        parts = module_name.split(".")
        output_file = self.config.output_dir.joinpath(*parts).with_suffix(".mdx")

        # Create parent directories if needed
        os.makedirs(output_file.parent, exist_ok=True)

        # Check if overwrite is allowed
        if not self.config.overwrite and output_file.exists():
            logger.warning(f"Skipping existing file: {output_file}")
            return output_file

        # Write content
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Written documentation for {module_name} to {output_file}")

        return output_file

    def generate_navigation(
        self, discovered_modules: Dict[str, object], parsed_modules: Dict[str, ModuleInfo]
    ) -> None:
        """
        Generate _meta.json files for Nextra navigation.

        Args:
            discovered_modules: Dictionary of discovered modules
            parsed_modules: Dictionary of parsed module information
        """
        logger.info("Generating navigation files")

        # Build directory structure
        directory_structure: Dict[str, Dict] = defaultdict(dict)
        directories_with_modules: Set[str] = set()

        # First pass: collect all modules and organize by directory
        for module_name in discovered_modules.keys():
            # Convert module name to path parts
            parts = module_name.split(".")

            # Keep track of directories that have modules
            if len(parts) > 1:
                # This is a submodule
                parent_dir = os.path.join(*parts[:-1])
                directories_with_modules.add(parent_dir)

            # Process each level of the module path
            for i in range(len(parts)):
                # Determine current directory and item name
                if i == 0:
                    # Root level
                    dir_path = ""
                    current_name = parts[0]
                else:
                    # Nested directory
                    dir_path = os.path.join(*parts[:i])
                    current_name = parts[i]

                # Skip adding if it would create both dir/module.mdx and dir/module/
                if i == len(parts) - 1:
                    # Add as a file
                    directory_structure[dir_path][current_name] = {
                        "title": f"{current_name}",
                        "type": "file",
                    }
                else:
                    # Add as a directory if not already present
                    if current_name not in directory_structure[dir_path]:
                        directory_structure[dir_path][current_name] = {
                            "title": f"{current_name}",
                            "type": "folder",
                        }

        # Second pass: create _meta.json file for each directory
        for dir_path, items in directory_structure.items():
            # Create the directory if it doesn't exist
            full_dir_path = os.path.join(self.config.output_dir, dir_path)
            os.makedirs(full_dir_path, exist_ok=True)

            # Prepare the meta file content
            meta_content: Dict[str, str] = {}

            # Add index first if it's a directory with submodules
            if self.config.create_index and (
                dir_path in directories_with_modules or dir_path == ""
            ):
                meta_content["index"] = "Overview"

                # Generate index.mdx file for this directory
                self._generate_directory_index(dir_path, items, discovered_modules, parsed_modules)

            # Add other items (excluding any that would create duplicates)
            for name, item_info in sorted(items.items()):
                if name != "index" and not self._would_create_duplicate(
                    dir_path, name, discovered_modules
                ):
                    meta_content[name] = item_info["title"]

            # Write the _meta.json file
            meta_file_path = os.path.join(full_dir_path, self.config.meta_filename)
            with open(meta_file_path, "w", encoding="utf-8") as f:
                json.dump(meta_content, f, indent=2)

            logger.info(
                f"Generated {self.config.meta_filename} for directory: {dir_path or 'root'}"
            )

    def _generate_directory_index(  # noqa: C901
        self,
        dir_path: str,
        items: Dict[str, Dict],
        discovered_modules: Dict[str, object],
        parsed_modules: Dict[str, ModuleInfo],
    ) -> None:
        """
        Generate an index.mdx file for a directory listing its modules.

        Args:
            dir_path: Path to the directory
            items: Dictionary of items in the directory
            discovered_modules: Dictionary of discovered modules
            parsed_modules: Dictionary of parsed module information
        """
        if not self.config.create_index:
            return

        # Create full path for the index file
        full_dir_path = os.path.join(self.config.output_dir, dir_path)
        index_path = os.path.join(full_dir_path, "index.mdx")

        # Check if overwrite is allowed
        if not self.config.overwrite and os.path.exists(index_path):
            logger.warning(f"Skipping existing index file: {index_path}")
            return

        # Determine the directory name for the title
        dir_name = os.path.basename(dir_path) if dir_path else "API Reference"

        # Build index content
        content = []
        content.append("import { Cards, Callout } from 'nextra/components'\n\n")
        content.append(f"# {dir_name.capitalize()} API Reference\n\n")

        # Try to get description from __init__.py if available
        init_module_name = dir_path.replace(os.path.sep, ".") if dir_path else None
        init_module_name = init_module_name.lstrip(".") if init_module_name else None

        if init_module_name and init_module_name in parsed_modules:
            module_info = parsed_modules[init_module_name]
            if module_info.docstring:
                # Add summary in callout
                if module_info.docstring.summary:
                    content.append(f"<Callout>\n{module_info.docstring.summary}\n</Callout>\n\n")

                # Add description
                if module_info.docstring.description:
                    content.append(f"{module_info.docstring.description}\n\n")

        # Get all direct modules in this directory
        modules_in_dir = []
        for name, info in items.items():
            if info["type"] == "file" and not self._would_create_duplicate(
                dir_path, name, discovered_modules
            ):
                module_full_name = (
                    f"{dir_path}.{name}".replace(os.path.sep, ".") if dir_path else name
                )
                module_full_name = module_full_name.lstrip(".")

                # Get module summary if available
                summary = ""
                if module_full_name in parsed_modules:
                    module_info = parsed_modules[module_full_name]
                    if module_info.docstring and module_info.docstring.summary:
                        summary = module_info.docstring.summary

                modules_in_dir.append((name, summary))

        # Get all subdirectories
        subdirs_in_dir = []
        for name, info in items.items():
            if info["type"] == "folder":
                subdir_module = f"{dir_path}.{name}".replace(os.path.sep, ".") if dir_path else name
                subdir_module = subdir_module.lstrip(".")

                # Try to get summary from directory's __init__.py if available
                summary = ""
                if subdir_module in parsed_modules:
                    module_info = parsed_modules[subdir_module]
                    if module_info.docstring and module_info.docstring.summary:
                        summary = module_info.docstring.summary

                subdirs_in_dir.append((name, summary))

        # Add modules and packages to the index
        if subdirs_in_dir:
            content.append("## Packages\n\n")
            content.append("<Cards>\n")
            for name, summary in sorted(subdirs_in_dir):
                content.append(f'  <Cards.Card title="{name}" href="./{name}"/>\n')
            content.append("</Cards>\n\n")

        if modules_in_dir:
            content.append("## Modules\n\n")
            content.append("<Cards>\n")
            for name, summary in sorted(modules_in_dir):
                content.append(f'  <Cards.Card title="{name}" href="./{name}"/>\n')
            content.append("</Cards>\n\n")

        # Write the index file
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("".join(content))

        logger.info(f"Generated index.mdx for directory: {dir_path or 'root'}")

    def _would_create_duplicate(
        self, dir_path: str, name: str, discovered_modules: Dict[str, object]
    ) -> bool:
        """
        Check if adding this item would create a duplicate name issue.

        Args:
            dir_path: Directory path
            name: Item name
            discovered_modules: Dictionary of discovered modules

        Returns:
            True if adding this item would create both dir/name.mdx and dir/name/
        """
        # Check if there's both a module and directory with the same name
        module_path = os.path.join(dir_path, name) if dir_path else name
        module_path = module_path.replace(os.path.sep, ".")
        module_path = module_path.lstrip(".")

        # Check if this exists as both a module and a directory prefix
        is_module = module_path in discovered_modules

        # Check if it's a directory prefix (has submodules)
        is_dir_prefix = any(
            mod_name.startswith(module_path + ".") for mod_name in discovered_modules
        )

        # If it's both a module and a directory, it would create a duplicate
        return is_module and is_dir_prefix
