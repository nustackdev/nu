"""
Output management for the Python API Reference Generator.

This module provides functionality to write MDX files and generate
navigation structures.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from ..config.models import OutputConfig
from ..core.models import ModuleInfo

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages writing MDX files and navigation structures."""

    # Constants for private module handling
    PRIVATE_PREFIX = "p__"
    PRIVATE_MARKER = "_"

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
        # Convert module name to path and handle private modules with "_" prefix
        parts = module_name.split(".")
        parts = [self._replace_private_names(part) for part in parts]
        output_file = self.config.output_dir.joinpath(*parts)

        # Create parent directories if needed
        os.makedirs(output_file, exist_ok=True)

        # Check if overwrite is allowed
        if not self.config.overwrite and output_file.exists():
            logger.warning(f"Skipping existing file: {output_file}")
            return output_file

        # Write content
        with open(output_file.joinpath("page.mdx"), "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Written documentation for {module_name} to {output_file}")

        return output_file

    def generate_navigation(
        self, discovered_modules: Dict[str, object], parsed_modules: Dict[str, ModuleInfo]
    ) -> None:
        """
        Generate _meta.js files for Nextra navigation.

        Args:
            discovered_modules: Dictionary of discovered modules
            parsed_modules: Dictionary of parsed module information
        """
        logger.info("Generating navigation files")

        # Build module tree
        module_tree = self._build_module_tree(discovered_modules)

        # Generate navigation files based on the tree
        self._write_navigation_files(module_tree, parsed_modules)

    def _build_module_tree(self, discovered_modules: Dict[str, object]) -> Dict:
        """
        Build a hierarchical tree structure from discovered modules.

        Args:
            discovered_modules: Dictionary of discovered modules

        Returns:
            Dictionary representing the module tree
        """
        module_tree = {}

        # Process all modules in a single pass
        for module_name in discovered_modules:
            parts = module_name.split(".")
            current = module_tree

            # Handle private modules with "_" prefix
            for i, part in enumerate(parts):
                parts[i] = self._replace_private_names(part)

            # Build tree path
            for i, part in enumerate(parts):
                is_leaf = i == len(parts) - 1

                if part not in current:
                    # Store the original name for later reference
                    original_name = part
                    if part.startswith(self.PRIVATE_PREFIX):
                        original_name = self._restore_private_names(part)

                    current[part] = {
                        "is_file": is_leaf,
                        "children": {},
                        "original_name": original_name,
                    }
                elif is_leaf:
                    # If we previously saw this as a directory, mark it as both
                    current[part]["is_file"] = True

                if not is_leaf:
                    current = current[part]["children"]

        return module_tree

    def _write_navigation_files(
        self, tree: Dict, parsed_modules: Dict[str, ModuleInfo], path: str = ""
    ) -> None:
        """
        Generate _meta.js files and index pages recursively.

        Args:
            tree: Module tree dictionary
            parsed_modules: Dictionary of parsed module information
            path: Current path in the tree
        """
        meta = {}

        # Add index if needed
        # if self.config.create_index:
        #     meta["index"] = "Overview"

        # Separate folders and files
        folders = []
        files = []

        for name, info in tree.items():
            # Add to appropriate list
            if info["is_file"] and not info["children"]:
                files.append(name)
            else:
                folders.append(name)

        # Add folders to meta
        for folder in sorted(folders):
            # Get the original name for display, but keep folder name for paths
            meta[folder] = ""

        # Add files to meta
        for file in sorted(files):
            # Get the original name for display, but keep file name for paths
            meta[file] = ""

        # Create output directory
        output_path = os.path.join(self.config.output_dir, path)
        os.makedirs(output_path, exist_ok=True)

        # Write _meta.js
        meta_file_path = os.path.join(output_path, "_meta.js")
        if path:
            with open(meta_file_path, "w", encoding="utf-8") as f:
                f.write(f"export default {json.dumps(meta, indent=2)}")

        logger.info(f"Generated _meta.js for directory: {path or 'root'}")

        # Generate index file if needed
        if self.config.create_index and path:
            self._generate_simple_index(path, folders, files, tree, parsed_modules)

        # Process subdirectories
        for folder in folders:
            folder_path = os.path.join(path, folder) if path else folder
            self._write_navigation_files(tree[folder]["children"], parsed_modules, folder_path)

    def _generate_simple_index(
        self,
        dir_path: str,
        folders: List[str],
        files: List[str],
        tree: Dict,
        parsed_modules: Dict[str, ModuleInfo],
    ) -> None:
        """
        Generate a simple index file listing subdirectories and modules.

        Args:
            dir_path: Directory path
            folders: List of folder names
            files: List of file names
            tree: Module tree dictionary
            parsed_modules: Dictionary of parsed module information
        """
        if not dir_path:
            return

        # Skip if overwrite not allowed and file exists
        full_path = os.path.join(self.config.output_dir, dir_path, "page.mdx")
        if not self.config.overwrite and os.path.exists(full_path):
            logger.warning(f"Skipping existing index file: {full_path}")
            return

        # Build index content
        content = []
        dir_name = os.path.basename(dir_path)

        # Fix displayed name for private modules
        dir_name = self._restore_private_names(dir_name)

        # Add frontmatter
        content.append("---\n")
        content.append(f"title: {dir_name}\n")
        content.append(f"sidebarTitle: 📦 {dir_name}\n")
        content.append("asIndexPage: true\n")
        content.append("---\n\n")

        content.append("import { Cards, Callout } from 'nextra/components'\n\n")
        content.append(f"# 📦 `{dir_name}` Reference\n\n")

        # Try to get description from __init__.py if available
        module_path = dir_path.replace(os.path.sep, ".")
        module_path = module_path.lstrip(".")

        # Convert prefixed paths back to original for lookup
        lookup_module_path = self._get_original_module_path(module_path)

        if lookup_module_path and lookup_module_path in parsed_modules:
            module_info = parsed_modules[lookup_module_path]
            if module_info.docstring:
                # Add summary in callout
                if module_info.docstring.summary:
                    content.append(f"<Callout>\n{module_info.docstring.summary}\n</Callout>\n\n")

                # Add description
                if module_info.docstring.description:
                    content.append(f"{module_info.docstring.description}\n\n")

        # Add packages section
        if folders:
            content.append("## Subpackages\n\n")
            content.append("<Cards>\n")
            for folder in sorted(folders):
                original_name = tree[folder].get("original_name", folder)
                display_name = self._restore_private_names(original_name)

                # Try to get summary
                folder_module = (
                    f"{dir_path}.{original_name}".replace(os.path.sep, ".")
                    if dir_path
                    else original_name
                )
                folder_module = folder_module.lstrip(".")

                # Convert prefixed paths back to original for lookup
                lookup_folder_module = self._get_original_module_path(folder_module)

                summary = ""

                if lookup_folder_module in parsed_modules:
                    module_info = parsed_modules[lookup_folder_module]
                    if module_info.docstring and module_info.docstring.summary:
                        summary = f" - {module_info.docstring.summary}"

                content.append(
                    f'  <Cards.Card title="{display_name}{summary}" href="/api/{dir_path}/{folder}"/>\n'
                )
            content.append("</Cards>\n\n")

        # Add modules section
        if files:
            content.append("## Modules\n\n")
            content.append("<Cards>\n")
            for file in sorted(files):
                original_name = tree[file].get("original_name", file)
                display_name = self._restore_private_names(original_name)

                # Try to get summary
                file_module = (
                    f"{dir_path}.{original_name}".replace(os.path.sep, ".")
                    if dir_path
                    else original_name
                )
                file_module = file_module.lstrip(".")

                # Convert prefixed paths back to original for lookup
                lookup_file_module = self._get_original_module_path(file_module)

                summary = ""

                if lookup_file_module in parsed_modules:
                    module_info = parsed_modules[lookup_file_module]
                    if module_info.docstring and module_info.docstring.summary:
                        summary = f": {module_info.docstring.summary}"

                content.append(
                    f'  <Cards.Card title="{display_name}{summary}" href="/api/{dir_path}/{file}" />\n'
                )
            content.append("</Cards>\n\n")

        # Write index file
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("".join(content))

        logger.info(f"Generated index page for directory: {dir_path or 'root'}")

    def _replace_private_names(self, name: str) -> str:
        """
        Replace private module names with prefixed versions.

        Args:
            name: Module name

        Returns:
            Modified module name with p__ prefix instead of _
        """
        if name.startswith(self.PRIVATE_MARKER):
            return f"{self.PRIVATE_PREFIX}{name[1:]}"
        return name

    def _restore_private_names(self, name: str) -> str:
        """
        Restore original private module names from prefixed versions.

        Args:
            name: Prefixed module name

        Returns:
            Original module name with _ prefix
        """
        if name.startswith(self.PRIVATE_PREFIX):
            return f"{self.PRIVATE_MARKER}{name[len(self.PRIVATE_PREFIX):]}"
        return name

    def _get_original_module_path(self, module_path: str) -> str:
        """
        Convert a path with p__ prefixes back to original form with _ prefixes.

        Args:
            module_path: Module path with p__ prefixes

        Returns:
            Original module path with _ prefixes
        """
        if not module_path:
            return module_path

        parts = module_path.split(".")
        parts = [self._restore_private_names(part) for part in parts]
        return ".".join(parts)
