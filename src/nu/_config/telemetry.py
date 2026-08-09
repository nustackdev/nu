"""Fire-and-forget PostHog capture, no runtime dependency.

POSTs one event to the PostHog capture endpoint on a daemon thread and
returns immediately. Silent on every failure (offline, host down,
malformed response) so a Nu program never blocks or crashes because of
telemetry.

Skipped when: telemetry is off in ``~/.nu/config.json``, we detect an
editable install (dev mode), or no PostHog token is configured. See
:mod:`nu._config.config`.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import threading
import urllib.request
from typing import TYPE_CHECKING

from . import config as _config


if TYPE_CHECKING:
    from typing import Any


# PostHog Project API key -- public write-only token, safe to embed
# (same one baked into the docs site's client bundle). Env var overrides
# for local testing against a different PostHog project.
_TOKEN = os.environ.get("NU_POSTHOG_TOKEN", "phc_yRpWfpoMeeRM8sKMPGPEsGy8ygNHJTpsGwrsikfpRfFz")
_HOST = os.environ.get("NU_POSTHOG_HOST", "https://t.nustack.dev").rstrip("/")


def _base_properties() -> dict[str, Any]:
    from nu import __version__

    return {
        "nu_version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system().lower(),
        "arch": platform.machine().lower(),
    }


FIRST_RUN_MARKER = _config.HOME / "first_run.sent"


def _post(payload: dict[str, Any], on_success: object = None) -> None:
    from nu import __version__

    req = urllib.request.Request(  # noqa: S310
        f"{_HOST}/i/v0/e/",
        data=json.dumps(payload).encode(),
        # Explicit User-Agent: Cloudflare's default bot rules block
        # ``Python-urllib/x.y`` with error 1010, dropping every POST.
        headers={"Content-Type": "application/json", "User-Agent": f"nu-py/{__version__}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310
            resp.read()
            status = getattr(resp, "status", 200)
    except Exception:
        return
    if 200 <= status < 300 and callable(on_success):
        try:
            on_success()
        except Exception:  # noqa: S110
            pass


def _fire(
    event: str,
    distinct_id: str,
    properties: dict[str, Any] | None = None,
    on_success: object = None,
) -> None:
    payload = {
        "api_key": _TOKEN,
        "event": event,
        "distinct_id": distinct_id,
        "properties": {**_base_properties(), **(properties or {})},
    }
    threading.Thread(target=_post, args=(payload, on_success), daemon=True).start()


def capture(event: str, properties: dict[str, Any] | None = None) -> None:
    """Queue a PostHog event. Loads config to check opt-out. Never raises."""
    try:
        if not _TOKEN or _config.is_dev_install() or not _config.telemetry_enabled():
            return
        _fire(event, _config.distinct_id(), properties)
    except Exception:  # noqa: S110
        pass


def _mark_first_run_sent() -> None:
    """Drop the empty marker file that stops future retries."""
    try:
        _config.HOME.mkdir(parents=True, exist_ok=True)
        FIRST_RUN_MARKER.touch()
    except Exception:  # noqa: S110
        pass


def capture_first_run(distinct_id: str) -> None:
    """Fire ``nu_first_run``; retried on future imports until PostHog acks.

    Daemon thread, so short-lived processes (``nu --help``,
    ``python -c "import nu"``) may drop the POST. The bootstrap in
    ``nu/__init__.py`` re-calls this on every import until the marker
    file at :data:`FIRST_RUN_MARKER` exists -- written only after a
    successful 2xx response.
    """
    try:
        if not _TOKEN or _config.is_dev_install():
            return
        _fire("nu_first_run", distinct_id, on_success=_mark_first_run_sent)
    except Exception:  # noqa: S110
        pass


def config_for_browser() -> dict[str, Any]:
    """Payload for the nudle ``/api/telemetry-config`` endpoint."""
    enabled = bool(_TOKEN) and _config.telemetry_enabled() and not _config.is_dev_install()
    return {
        "enabled": enabled,
        "distinct_id": _config.distinct_id(),
        "posthog_token": _TOKEN if enabled else "",
        "posthog_host": _HOST,
        **_base_properties(),
    }
