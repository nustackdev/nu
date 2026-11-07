"""Anonymous nudle usage telemetry: one config file, one route, nothing sent from here.

The kernel sends nothing, and neither does this module. nudle, the browser
host, owns telemetry: the SPA sends one ``nudle_opened`` event per page load,
and the ``/api/telemetry-config`` route here tells it whether it may and what
to send with.

State lives in ``~/.nudle/config.json``: the ``telemetry`` flag (default on)
and a stable anonymous ``distinct_id``.

Opt-out: ``NUDLE_TELEMETRY=0`` (or ``false`` / ``off`` / ``no``) wins over
the config flag; ``1`` / ``true`` / ``on`` forces it on over the flag.
``DO_NOT_TRACK`` (the cross tool convention), ``CI`` and the variables the
major CIs set of their own turn it off whatever else says, so nobody's
pipeline is counted as use. Nothing is sent from an editable install or a
source tree without an install record (``NUDLE_DEV=1`` / ``0`` overrides
that guess). The browser sends only what this side allows: the config
route hands it no token and no id while telemetry is off here.

Every failure is swallowed: telemetry never blocks or breaks a program.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import uuid
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route


__all__ = [
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


# ---- the browser side -------------------------------------------------------


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


_OFF_PAYLOAD: dict[str, Any] = {"enabled": False}


def config_for_browser() -> dict[str, Any]:
    """What ``/api/telemetry-config`` returns; the SPA sends only when ``enabled``.

    Off here means off there: just ``{"enabled": false}``, no token, no host,
    no id, so the browser has nothing to send with. Never raises; a failure
    reads as off.
    """
    try:
        if not _active():
            return dict(_OFF_PAYLOAD)
        return {
            "enabled": True,
            "distinct_id": ensure_config()["distinct_id"],
            "posthog_token": posthog_token(),
            "posthog_host": posthog_host(),
            **_base_properties(),
        }
    except Exception:
        return dict(_OFF_PAYLOAD)


async def _telemetry_config(request: Request) -> JSONResponse:
    from starlette.responses import JSONResponse

    del request
    return JSONResponse(config_for_browser())


def route() -> Route:
    """``GET /api/telemetry-config``, for the ws server's ``routes=``."""
    from starlette.routing import Route

    return Route("/api/telemetry-config", _telemetry_config, methods=["GET"])
