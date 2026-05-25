"""Test-tree conventions for ``nu2``.

Layout: mirrors ``src/nu2/`` for unit tests, with a top-level ``integration/``
directory for cross-module flow tests. Shared helpers (tiny Term subclasses,
builders) live under ``_support/``, a package imported as
``from _support.terms import Leaf`` from any test file under ``tests/nu2/``.
The leading underscore keeps pytest from auto-collecting it as tests; the
``pythonpath = ["tests/nu2"]`` entry in ``pyproject.toml`` makes it
importable.

Concretely:

::

    tests/nu2/
    |-- conftest.py            <- this file
    |-- _support/              <- shared helpers (package)
    |   |-- __init__.py
    |   `-- terms.py           <- tiny canonical Term subclasses
    |-- engine/
    |   |-- conftest.py        <- engine-scoped fixtures
    |   |-- structure/         <- unit tests for src/nu2/engine/structure/
    |   |-- compilation/       <- ... for src/nu2/engine/compilation/
    |   |-- validation/
    |   `-- evaluation/
    |-- lang/
    |-- core/
    `-- integration/
        |-- conftest.py        <- integration fixtures (real Nu schema, ...)
        `-- ...

Conventions:

- **No ``__init__.py`` under ``tests/nu2/`` (except in ``_support/``).** With
  ``--import-mode=importlib`` (set in pyproject) pytest discovers tests by
  path, not by package import. Adding ``__init__.py`` causes import-mode
  conflicts as the tree grows; do not add them.
- **One test file per source module.** Mirror the source path:
  ``tests/nu2/engine/structure/test_attribute.py`` tests
  ``src/nu2/engine/structure/attribute.py``.
- **Unit vs integration.** A unit test exercises one module's public API.
  A test that builds a real Nu schema, compiles a Term, and drives the
  Runtime is an integration test and belongs under ``integration/``.
- **Fixtures over setup classes.** Prefer ``@pytest.fixture``.
- **Parametrize over duplication.** Use ``@pytest.mark.parametrize`` rather
  than copy-pasted test bodies.
- **Marks.** Use ``@pytest.mark.slow`` for tests that take noticeable wall
  time. Integration tests get the ``integration/`` location; they need no
  marker unless they are also slow.
"""

from __future__ import annotations
