"""The errors kv raises on its own: a bad address, and a term no bracket fits.

Everything else a kv read or write can raise comes from the layer that found
it: Python's ``KeyError`` for a key that is not there, the storage's own
errors for a lost commit.
"""

from __future__ import annotations


__all__ = [
    "BracketError",
    "NullAddressError",
]


class NullAddressError(LookupError):
    """A read, a write or a watch under a ref path with a NULL segment.

    A segment is NULL when the key it was given read nothing, eg an id looked
    up in an index that has no entry for it. The path then addresses nothing,
    so any access through it raises this, and nothing is read or written.
    Branch on the key first: ``If(IsNull(key), NullForm.create(), ...)``.

    Example:
        State.rows[Index.by_key["gone"]].count  # raises this
        State.rows[Index.by_key["gone"]].count.set(1)  # raises this
    """


class BracketError(ValueError):
    """``atomic`` was handed a term it cannot make one commit per store.

    Raised at build, while the bracket is being placed, for one of two terms:

    - one that writes two stores. One bracket commits to one store, so
      writing both is two commits: bracket each write on its own.
    - one that holds a write bracket on the store it also writes outside that
      bracket. Two transactions on one store never join, so the outer one
      could not take in what the inner one commits.
    """
