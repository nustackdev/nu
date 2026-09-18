"""Internal: ``~/.nu`` user config and anonymous usage telemetry.

Layout:

- :mod:`nu._config.constants` -- all paths, defaults, and PostHog
  wiring. Single source of truth.
- :mod:`nu._config.config` -- read/write ``~/.nu/config.json``,
  telemetry opt-out flag, stable ``distinct_id``.
- :mod:`nu._config.telemetry` -- fire-and-forget PostHog capture.

Hot path: :func:`bootstrap` does one ``exists()`` syscall and returns
immediately when the first-run marker is already in place; the config
and telemetry submodules are only imported on first-run bootstrap and
explicit CLI / nudle calls.
"""

from .constants import CONFIG_PATH as CONFIG_PATH
from .constants import FIRST_RUN_MARKER_PATH as FIRST_RUN_MARKER_PATH
from .constants import HOME as HOME


def bootstrap() -> None:
    """First-touch bootstrap for ``~/.nu``.

    Fast path: one ``exists()`` syscall on the first-run marker; the
    marker is only written after a successful capture, which itself
    only runs once the config file exists, so its presence implies
    both are in place.

    Otherwise: create the config on first ever import, and (re)fire
    the first-run event on every import until the POST gets a 2xx and
    drops the marker. That covers short-lived commands
    (``nu --help``, ``python -c "import nu"``) where a daemon POST
    would otherwise be killed on process exit. Silent on any failure.
    """
    try:
        if FIRST_RUN_MARKER_PATH.exists():
            return
        from .telemetry import capture_first_run

        if not CONFIG_PATH.exists():
            from .config import create_default

            capture_first_run(create_default())
        else:
            from .config import distinct_id

            capture_first_run(distinct_id())
    except Exception:  # noqa: S110
        pass
