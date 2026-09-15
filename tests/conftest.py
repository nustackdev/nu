"""Test-tree conventions for ``nu``.

Layout: one directory per distribution, each mirroring that package's source
tree, plus the directories for concerns that cross packages. Shared helpers
(tiny Term subclasses, builders) live under ``_lib/_support/``, a package
imported as ``from _support.terms import Leaf`` from any test file here.

``_support`` sits one level down for a reason. Making it importable by a bare
name means putting its parent on ``sys.path`` (the ``pythonpath`` entry in
``pyproject.toml``), and everything in that parent then becomes a candidate
top-level module name. Point it at ``tests/`` and ``nucore`` / ``nustd``
become importable names competing with the real packages; point it at
``tests/_lib``, which holds nothing else, and nothing can collide. The
underscores also keep pytest from collecting either as tests.

Concretely:

::

    tests/
    |-- conftest.py            <- this file
    |-- _lib/                  <- the one directory on sys.path
    |   `-- _support/          <- shared helpers (package)
    |       |-- __init__.py
    |       `-- terms.py       <- tiny canonical Term subclasses
    |-- nucore/                <- mirrors packages/nucore/src/nu/
    |   |-- engine/
    |   |   |-- conftest.py    <- engine-scoped fixtures
    |   |   |-- structure/     <- unit tests for src/nu/engine/structure/
    |   |   |-- compilation/   <- ... for src/nu/engine/compilation/
    |   |   |-- validation/
    |   |   `-- evaluation/
    |   |-- lang/
    |   `-- core/
    |-- nustd/                 <- mirrors packages/nustd/src/nustd/
    |   |-- kv/
    |   |-- ui/
    |   `-- test_uuid.py       <- the stdlib mirrors are one file each
    |-- narrowing/             <- type narrowing, spans both packages
    `-- integration/
        |-- conftest.py        <- integration fixtures (real Nu schema, ...)
        `-- ...

``nucli`` has no tests yet; it gets a directory when it does.

Conventions:

- **No ``__init__.py`` under ``tests/`` (except in ``_lib/_support/``).** With
  ``--import-mode=importlib`` (set in pyproject) pytest discovers tests by
  path, not by package import. Adding ``__init__.py`` causes import-mode
  conflicts as the tree grows; do not add them.
- **One test file per source module.** Mirror the source path:
  ``tests/nucore/engine/structure/test_attribute.py`` tests
  ``packages/nucore/src/nu/engine/structure/attribute.py``.
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
