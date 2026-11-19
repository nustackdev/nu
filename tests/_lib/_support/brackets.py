"""Read a lifecycle bracket's config children by name, for tests that inspect a spec.

A bracket's children are ``[body, *config]``; its ``_aopen`` names the config
values after ``ctx``. ``config(b)`` evaluates them the way the bracket does on
entry and keys each by that name.
"""

from __future__ import annotations

import inspect

from nu.lang import Context


def config(bracket: object) -> dict[str, object]:
    """The bracket's config values keyed by its ``_aopen`` parameter names."""
    params = list(inspect.signature(type(bracket)._aopen).parameters)[2:]
    return dict(zip(params, bracket._config_values(Context()), strict=True))
