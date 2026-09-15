"""Shared test-support package for ``tests``.

Importable as ``from _support.<module> import <name>`` from any test under
``tests/`` thanks to the ``pythonpath = ["tests/_lib"]`` entry in
``pyproject.toml``. It lives under ``_lib/`` so that entry exposes nothing
but this package -- see ``tests/conftest.py``. The leading underscore keeps
pytest from collecting this directory as tests.

Add a new module when a helper is needed in more than one test file. Do
not put helpers here speculatively -- inline them in the test that needs
them until a second caller appears.
"""

from __future__ import annotations
