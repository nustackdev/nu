"""Anonymous nudle usage telemetry: one config file, one fire-and-forget POST.

The kernel sends nothing. nudle, the browser host, owns this: a first-run
event when the server first starts, and the ``/api/telemetry-config`` route
the SPA reads before it sends its own ``nudle_opened`` ping.

State lives in ``~/.nudle/``:

- ``config.json`` -- the ``telemetry`` flag (default on) and a stable
  anonymous ``distinct_id``.
- ``first_run.sent`` -- dropped after PostHog acks the first-run event, so
  it is retried on every start until then.

Opt-out: ``NUDLE_TELEMETRY=0`` (or ``false`` / ``off`` / ``no``) wins over
the config flag; ``1`` / ``true`` / ``on`` forces it on over the flag.
``DO_NOT_TRACK`` (the cross tool convention), ``CI`` and the variables the
major CIs set of their own turn it off whatever else says, so nobody's
pipeline is counted as use. Nothing is sent from an editable install or a
source tree without an install record (``NUDLE_DEV=1`` / ``0`` overrides
that guess). The browser sends only what this side allows: the config
route hands it no token while telemetry is off here.

Only the events in :data:`EVENTS` ever leave; anything else is dropped.
Every failure is swallowed: telemetry never blocks or breaks a program.
"""

from __future__ import annotations

import json
import os
import platform
import ssl
import sys
import threading
import urllib.request
import uuid
from datetime import datetime, timezone
from functools import cache
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route


__all__ = [
    "EVENTS",
    "capture",
    "capture_first_run",
    "config_for_browser",
    "is_dev_install",
    "posthog_host",
    "posthog_token",
    "route",
    "set_telemetry",
    "telemetry_enabled",
]


# PostHog project API key: a public write-only token, safe to embed (the
# docs site bundles the same one). The one copy of it: the browser gets it
# from ``/api/telemetry-config``. Env vars point a local run elsewhere.
POSTHOG_TOKEN = "phc_yRpWfpoMeeRM8sKMPGPEsGy8ygNHJTpsGwrsikfpRfFz"  # noqa: S105 -- public by design
POSTHOG_HOST = "https://t.nustack.dev"
POSTHOG_BATCH_PATH = "/batch/"

FIRST_RUN_EVENT = "nudle_first_run"
OPENED_EVENT = "nudle_opened"

#: Every event nudle sends, from here or from the browser. Nothing else leaves.
EVENTS = frozenset({FIRST_RUN_EVENT, OPENED_EVENT})

HTTP_TIMEOUT_SECONDS = 3

_ENV_FLAG = "NUDLE_TELEMETRY"
_OFF = frozenset({"0", "false", "off", "no"})
_ON = frozenset({"1", "true", "on"})

# Off when set to anything but empty or off, whatever the flag says: the
# cross tool convention, then ``CI`` and the variables CIs set of their own.
_OFF_WHEN_SET = (
    "DO_NOT_TRACK",
    "CI",
    "GITHUB_ACTIONS",
    "GITLAB_CI",
    "BUILDKITE",
    "CIRCLECI",
    "TF_BUILD",
    "JENKINS_URL",
    "TEAMCITY_VERSION",
    "CODEBUILD_BUILD_ID",
    "BITBUCKET_BUILD_NUMBER",
)


def posthog_token() -> str:
    """The project key, from ``NUDLE_POSTHOG_TOKEN`` when set."""
    return os.environ.get("NUDLE_POSTHOG_TOKEN", POSTHOG_TOKEN)


def posthog_host() -> str:
    """The capture host, from ``NUDLE_POSTHOG_HOST`` when set, no trailing slash."""
    return os.environ.get("NUDLE_POSTHOG_HOST", POSTHOG_HOST).rstrip("/")


# ---- config -----------------------------------------------------------------


def home() -> Path:
    """``~/.nudle``, resolved on each call so a changed ``HOME`` is honoured."""
    return Path.home() / ".nudle"


def config_path() -> Path:
    return home() / "config.json"


def first_run_marker() -> Path:
    return home() / "first_run.sent"


def load() -> dict[str, Any]:
    """The config file as a dict; ``{}`` when missing or unreadable."""
    try:
        cfg = json.loads(config_path().read_text())
    except (OSError, ValueError):
        return {}
    return cfg if isinstance(cfg, dict) else {}


def save(cfg: dict[str, Any]) -> None:
    """Write the config atomically (temp file, then rename)."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def ensure_config() -> dict[str, Any]:
    """The config, written with defaults and a fresh ``distinct_id`` if absent."""
    cfg = load()
    if isinstance(cfg.get("distinct_id"), str) and cfg["distinct_id"]:
        return cfg
    cfg = {"telemetry": True, **cfg, "distinct_id": str(uuid.uuid4())}
    save(cfg)
    return cfg


def distinct_id() -> str:
    did = load().get("distinct_id")
    return did if isinstance(did, str) and did else "unknown"


def env_override() -> str | None:
    """The environment variable turning telemetry off right now, None when none does."""
    if os.environ.get(_ENV_FLAG, "").strip().lower() in _OFF:
        return _ENV_FLAG
    for name in _OFF_WHEN_SET:
        if os.environ.get(name, "").strip().lower() not in {"", *_OFF}:
            return name
    return None


def telemetry_enabled() -> bool:
    """The effective flag: off by the environment, forced on by ``NUDLE_TELEMETRY``, else the file."""
    if env_override() is not None:
        return False
    if os.environ.get(_ENV_FLAG, "").strip().lower() in _ON:
        return True
    return bool(load().get("telemetry", True))


def set_telemetry(on: bool) -> None:
    """Flip the config flag, keeping the rest of the file."""
    cfg = ensure_config()
    cfg["telemetry"] = bool(on)
    save(cfg)


def is_dev_install() -> bool:
    """True when ``nustd`` runs from a source checkout: editable, or not installed at all.

    Reads the installer's ``direct_url.json``, so a wheel installed from a
    local path still counts as a release. ``NUDLE_DEV=1`` forces dev mode,
    ``NUDLE_DEV=0`` forces a release install.
    """
    override = os.environ.get("NUDLE_DEV")
    if override == "1":
        return True
    if override == "0":
        return False
    try:
        raw = metadata.distribution("nustd").read_text("direct_url.json")
    except metadata.PackageNotFoundError:
        return True
    except Exception:
        return False
    try:
        return bool(raw and json.loads(raw).get("dir_info", {}).get("editable", False))
    except Exception:
        return False


def _active() -> bool:
    return bool(posthog_token()) and not is_dev_install() and telemetry_enabled()


# ---- sending ----------------------------------------------------------------


def _version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _base_properties() -> dict[str, Any]:
    from nu import __version__ as nu_version

    v = sys.version_info
    return {
        "product": "nudle",
        "nudle_version": _version("nudle"),
        "nu_version": nu_version,
        "python_version": f"{v.major}.{v.minor}.{v.micro}",
        "platform": platform.system().lower(),
        "arch": platform.machine().lower(),
    }


@cache
def _ssl_context() -> ssl.SSLContext:
    """The platform's CAs and certifi's together, made once per process.

    python.org's macOS builds ship no system CA bundle, so the platform
    alone trusts nothing there. certifi alone misses the roots a company
    network adds to the system store. Both, so either one is enough.
    """
    context = ssl.create_default_context()
    try:
        import certifi

        context.load_verify_locations(cafile=certifi.where())
    except Exception:
        pass
    return context


def _post(payload: dict[str, Any], on_success: Callable[[], None] | None = None) -> None:
    req = urllib.request.Request(  # noqa: S310
        f"{posthog_host()}{POSTHOG_BATCH_PATH}",
        data=json.dumps(payload).encode(),
        # Explicit User-Agent: Cloudflare's default bot rules block
        # ``Python-urllib/x.y`` with error 1010, dropping every POST.
        headers={
            "Content-Type": "application/json",
            "User-Agent": f"nudle-py/{_version('nudle') or '0.0.0+dev'}",
        },
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
    if 200 <= status < 300 and on_success is not None:
        try:
            on_success()
        except Exception:
            pass


def _fire(
    event: str,
    did: str,
    properties: dict[str, Any] | None = None,
    on_success: Callable[[], None] | None = None,
) -> None:
    if event not in EVENTS:
        return
    payload = {
        "api_key": posthog_token(),
        "batch": [
            {
                "event": event,
                "distinct_id": did,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "properties": {**_base_properties(), **(properties or {})},
            }
        ],
    }
    threading.Thread(
        target=_post, args=(payload, on_success), name="nudle-telemetry", daemon=True
    ).start()


def capture(event: str, properties: dict[str, Any] | None = None) -> None:
    """Queue one of :data:`EVENTS` on a daemon thread, unless opted out. Never raises.

    Any other name is dropped silently.
    """
    try:
        if event in EVENTS and _active():
            _fire(event, ensure_config()["distinct_id"], properties)
    except Exception:
        pass


def _mark_first_run_sent() -> None:
    try:
        marker = first_run_marker()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    except Exception:
        pass


def capture_first_run() -> None:
    """Send the first-run event, retried on every start until PostHog acks.

    The marker is only written after a 2xx, so a start that is killed before
    the daemon thread lands simply tries again next time. Never raises.
    """
    try:
        if first_run_marker().exists() or not _active():
            return
        _fire(FIRST_RUN_EVENT, ensure_config()["distinct_id"], on_success=_mark_first_run_sent)
    except Exception:
        pass


# ---- the browser side -------------------------------------------------------


def config_for_browser() -> dict[str, Any]:
    """What ``/api/telemetry-config`` returns; the SPA sends only when ``enabled``.

    Off here means off there: no token, no id, so the browser has nothing to
    send with. Never raises; a failure reads as off.
    """
    try:
        enabled = _active()
        return {
            "enabled": enabled,
            "distinct_id": ensure_config()["distinct_id"] if enabled else "",
            "posthog_token": posthog_token() if enabled else "",
            "posthog_host": posthog_host(),
            **_base_properties(),
        }
    except Exception:
        return {"enabled": False, "distinct_id": "", "posthog_token": "", "posthog_host": ""}


async def _telemetry_config(request: Request) -> JSONResponse:
    from starlette.responses import JSONResponse

    del request
    return JSONResponse(config_for_browser())


def route() -> Route:
    """``GET /api/telemetry-config``, for the ws server's ``routes=``."""
    from starlette.routing import Route

    return Route("/api/telemetry-config", _telemetry_config, methods=["GET"])


class FirstRun:
    """Fires :func:`capture_first_run` when the serve tree is entered.

    A setup-only fabric, so the ping goes out when the server actually
    starts rather than when a module is imported or a term is built.
    """

    def setup(self, ctx: object) -> None:
        del ctx
        capture_first_run()
