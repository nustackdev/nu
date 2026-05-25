"""Unit tests for ``nu2.lang.args``.

Covers the argument type aliases -- ``Arg[T]`` and the scalar / collection
specializations -- as structural type checks: each alias resolves to the
expected ``T | Nu[T] | Sentinel`` union.
"""

from __future__ import annotations
