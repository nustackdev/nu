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
import platform
import ssl
import sys
import threading
import urllib.request
from typing import TYPE_CHECKING

from . import config as _config
from .constants import (
    FIRST_RUN_EVENT,
    FIRST_RUN_MARKER_PATH,
    HOME,
    HTTP_TIMEOUT_SECONDS,
    POSTHOG_CAPTURE_PATH,
    POSTHOG_HOST,
    POSTHOG_TOKEN,
)


if TYPE_CHECKING:
    from typing import Any


def _ssl_context() -> ssl.SSLContext:
    # python.org macOS installers ship without a system CA bundle, so
    # the default context has zero trust roots and every HTTPS POST
    # fails CERTIFICATE_VERIFY_FAILED. Prefer certifi's bundle when it
    # is importable; fall back to the platform default otherwise.
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _base_properties() -> dict[str, Any]:
    from nu import __version__

    return {
        "nu_version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system().lower(),
        "arch": platform.machine().lower(),
    }


def _post(payload: dict[str, Any], on_success: object = None) -> None:
    from nu import __version__

    req = urllib.request.Request(  # noqa: S310
        f"{POSTHOG_HOST}{POSTHOG_CAPTURE_PATH}",
        data=json.dumps(payload).encode(),
        # Explicit User-Agent: Cloudflare's default bot rules block
        # ``Python-urllib/x.y`` with error 1010, dropping every POST.
        headers={"Content-Type": "application/json", "User-Agent": f"nu-py/{__version__}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(  # noqa: S310
            req, timeout=HTTP_TIMEOUT_SECONDS, context=_ssl_context()
        ) as resp:
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
        "api_key": POSTHOG_TOKEN,
        "event": event,
        "distinct_id": distinct_id,
        "properties": {**_base_properties(), **(properties or {})},
    }
    threading.Thread(target=_post, args=(payload, on_success), daemon=True).start()


def capture(event: str, properties: dict[str, Any] | None = None) -> None:
    """Queue a PostHog event. Loads config to check opt-out. Never raises."""
    try:
        if not POSTHOG_TOKEN or _config.is_dev_install() or not _config.telemetry_enabled():
            return
        _fire(event, _config.distinct_id(), properties)
    except Exception:  # noqa: S110
        pass


def _mark_first_run_sent() -> None:
    """Drop the empty marker file that stops future retries."""
    try:
        HOME.mkdir(parents=True, exist_ok=True)
        FIRST_RUN_MARKER_PATH.touch()
    except Exception:  # noqa: S110
        pass


def capture_first_run(distinct_id: str) -> None:
    """Fire the first-run event; retried on future imports until PostHog acks.

    Daemon thread, so short-lived processes (``nu --help``,
    ``python -c "import nu"``) may drop the POST. The bootstrap in
    :mod:`nu._config` re-calls this on every import until the marker
    file at :data:`FIRST_RUN_MARKER_PATH` exists -- written only after
    a successful 2xx response.
    """
    try:
        if not POSTHOG_TOKEN or _config.is_dev_install():
            return
        _fire(FIRST_RUN_EVENT, distinct_id, on_success=_mark_first_run_sent)
    except Exception:  # noqa: S110
        pass


def config_for_browser() -> dict[str, Any]:
    """Payload for the nudle ``/api/telemetry-config`` endpoint."""
    enabled = bool(POSTHOG_TOKEN) and _config.telemetry_enabled() and not _config.is_dev_install()
    return {
        "enabled": enabled,
        "distinct_id": _config.distinct_id(),
        "posthog_token": POSTHOG_TOKEN if enabled else "",
        "posthog_host": POSTHOG_HOST,
        **_base_properties(),
    }
