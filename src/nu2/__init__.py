"""Nu, the layered rewrite.

This package is the in-development successor to ``nu2``. Three layers:

- ``nu2.engine`` - layer 0, the domain-free Symbol + Attribute engine plus
  the generic execution driver.
- ``nu2.lang`` - layer 1, Nu the language on top of the engine.
- ``nu2.core`` - layer 2, the concrete atoms a real program is built from.

Importers should reach into the subpackages; this root re-exports nothing.
At swap time ``nu2`` becomes ``nu2``.
"""
