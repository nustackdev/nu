"""Nu, the layered rewrite.

This package is the in-development successor to ``nu``. Three layers:

- ``nu.engine`` - layer 0, the domain-free Term + Attribute engine plus
  the generic execution driver.
- ``nu.lang`` - layer 1, Nu the language on top of the engine.
- ``nu.core`` - layer 2, the concrete atoms a real program is built from.

Importers should reach into the subpackages; this root re-exports nothing.
At swap time ``nu`` becomes ``nu``.
"""
