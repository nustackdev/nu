#!/usr/bin/env python3
"""
Setup script for everyshape.
"""

from pathlib import Path

from setuptools import find_packages, setup


def main() -> None:
    setup(
        name="everyshape",
        version="1.1.0",
        author="Gor Arakelyan",
        description="Persistent, reactive Shapes for Python",
        long_description=Path("README.md").read_text(),
        long_description_content_type="text/markdown",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        include_package_data=True,
    )


if __name__ == "__main__":
    main()
