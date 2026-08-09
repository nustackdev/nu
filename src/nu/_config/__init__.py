"""Internal: ``~/.nu`` user config and anonymous usage telemetry.

Two submodules:

- :mod:`nu._config.config` -- read/write ``~/.nu/config.json``,
  telemetry opt-out flag, stable ``distinct_id``.
- :mod:`nu._config.telemetry` -- fire-and-forget PostHog capture.

Hot path: ``nu/__init__.py`` only does ``CONFIG_PATH.exists()`` and
skips both submodules entirely on subsequent imports. The load / write
code paths only run on first-run bootstrap and explicit CLI / nudle
calls.
"""

from .config import CONFIG_PATH as CONFIG_PATH
from .config import HOME as HOME
