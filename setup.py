#!/usr/bin/env python3
"""
Setup script for redwood with Cython support.
"""

import os
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup


def get_extensions():
    """Find and compile all .pyx files in the codec subpackage."""
    extensions = []

    # Find all .pyx files in the src directory
    src_dir = Path("src/redwood")
    if src_dir.exists():
        pyx_files = list(src_dir.glob("*.pyx"))

        for pyx_file in pyx_files:
            # Convert path to module name
            module_path = str(pyx_file.with_suffix("")).replace(os.sep, ".")
            # Remove 'src.' prefix
            if module_path.startswith("src."):
                module_path = module_path[4:]

            extension = Extension(
                module_path,
                [str(pyx_file)],
                language_level=3,
            )
            extensions.append(extension)

    return extensions


def main():
    # Get extensions
    extensions = get_extensions()

    # Only cythonize if we have .pyx files
    if extensions:
        extensions = cythonize(
            extensions,
            compiler_directives={
                "language_level": 3,
                "embedsignature": True,
                "boundscheck": False,  # Disable bounds checking for performance
                "wraparound": False,  # Disable wraparound for performance
                "initializedcheck": False,  # Disable initialization checking
                "cdivision": True,  # Use C division semantics
            },
            build_dir="build",
        )

    setup(
        ext_modules=extensions,
        zip_safe=False,  # Required for Cython extensions
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        include_package_data=True,
    )


if __name__ == "__main__":
    main()
