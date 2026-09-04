"""User config at ``~/.nu/config.json``.

One JSON file, machine-managed. Holds the telemetry opt-out flag and a
stable anonymous ``distinct_id``. Created on first `nu` import or CLI
run; that first-touch is the signal that a human actually installed
and used Nu (see :mod:`nu._config.telemetry`).
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from .constants import CONFIG_DEFAULTS, CONFIG_PATH, HOME


if TYPE_CHECKING:
    from typing import Any


def load() -> dict[str, Any]:
    """Read the config file; return {} if it does not exist or is unreadable."""
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save(cfg: dict[str, Any]) -> None:
    """Write config atomically (temp + rename)."""
    HOME.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n")
    tmp.replace(CONFIG_PATH)


def create_default() -> str:
    """Create the config with defaults; return the new distinct_id.

    Caller must have checked that :data:`CONFIG_PATH` does not exist --
    this always writes.
    """
    did = str(uuid.uuid4())
    save({**CONFIG_DEFAULTS, "distinct_id": did})
    return did


def telemetry_enabled() -> bool:
    """Effective telemetry state (config flag, defaulting on)."""
    return bool(load().get("telemetry", True))


def set_telemetry(on: bool) -> None:
    """Flip the telemetry flag, preserving the rest of the config."""
    cfg = load() or {**CONFIG_DEFAULTS, "distinct_id": str(uuid.uuid4())}
    cfg["telemetry"] = bool(on)
    save(cfg)


def distinct_id() -> str:
    """Stable anonymous id. Generated on first :func:`create_default` call."""
    did = load().get("distinct_id")
    if isinstance(did, str) and did:
        return did
    return "unknown"


def is_dev_install() -> bool:
    """True when Nu is imported from a source checkout (editable install).

    Heuristic: a ``pyproject.toml`` sits within a few levels above
    ``nu/__init__.py`` (the ``src/nu`` layout used in this repo). Env
    override ``NU_DEV=1`` forces dev mode; ``NU_DEV=0`` forces prod.
    """
    override = os.environ.get("NU_DEV")
    if override == "1":
        return True
    if override == "0":
        return False
    here = Path(__file__).resolve()
    for depth in (3, 4, 5):
        if depth >= len(here.parents):
            break
        if (here.parents[depth] / "pyproject.toml").exists():
            return True
    return False
