"""Shared test-support package for ``tests/nu``.

Importable as ``from _support.<module> import <name>`` from any test under
``tests/nu/`` thanks to the ``pythonpath = ["tests/nu"]`` entry in
``pyproject.toml``. The leading underscore keeps pytest from collecting
this directory as tests.

Add a new module when a helper is needed in more than one test file. Do
not put helpers here speculatively -- inline them in the test that needs
them until a second caller appears.
"""

from __future__ import annotations
