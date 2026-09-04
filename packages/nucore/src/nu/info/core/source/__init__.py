"""What the code says: a Python object, introspected.

One module per thing the code can be asked, each with its reader and the value
that reader produces. No docstrings are touched here, and nothing knows about
Nu.

- ``signature`` reads a callable's parameters, defaults and variadic tails.
- ``module`` enumerates a module's public members.
- ``code`` fetches source text and location.
- ``unpack`` reads how many names a function unpacks a variable into, for the
  structural facts a signature does not carry.
"""

from __future__ import annotations

from nu.info.core.source.code import Source, read_location, read_source
from nu.info.core.source.module import Member, public_members
from nu.info.core.source.mro import Binding, walk_bindings
from nu.info.core.source.signature import Param, Signature, read_signature
from nu.info.core.source.unpack import unpacked_count


__all__ = [
    "Binding",
    "Member",
    "Param",
    "Signature",
    "Source",
    "public_members",
    "read_location",
    "read_signature",
    "read_source",
    "unpacked_count",
    "walk_bindings",
]
