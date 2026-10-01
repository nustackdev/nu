"""The attrs axis of the Context fabric: how an interaction hands values to its body.

``ctx.attrs`` is a channel, not a store. An interaction binds its own internal
values there for its body: a loop its item, a fold its accumulator, a catch the
error, a retry the attempt, a reaction the key that changed. Only interactions
write it, imperatively in their compile through ``ctx.attrs.let`` / ``set``.
The tree only reads, through ``Attr(name)``, and ``Attr(name).exists()`` asks
whether a name is bound. A body given as a lambda gets those reads as its
parameters, over names the interaction mints (``binders``). State of any kind goes through a fabric instead:
``nu.mem`` for local state, kv for records.

What an interaction hands over is immutable. Concurrent tasks share bound
values by reference, so a container the interaction builds itself is bound in
an immutable form (a tuple, a frozenset, a read-only mapping, plain scalars);
a value that comes from user data passes through as it is.
"""

from __future__ import annotations

from .interactions import AttrExists
from .refs import Attr


__all__ = ["Attr", "AttrExists"]
