"""Single source of truth for ``~/.nu`` paths and PostHog wiring.

Everything the ``_config`` subpackage would otherwise hardcode lives
here: filesystem layout under ``~/.nu``, config defaults, and the
PostHog capture endpoint. Env vars ``NU_POSTHOG_TOKEN`` /
``NU_POSTHOG_HOST`` override the baked-in defaults (local testing
against a different PostHog project).
"""

from __future__ import annotations

import os
from pathlib import Path


HOME = Path.home() / ".nu"
CONFIG_PATH = HOME / "config.json"
DEMOS_DIR = HOME / "demos"
FIRST_RUN_MARKER_PATH = HOME / "first_run.sent"

CONFIG_DEFAULTS: dict[str, object] = {"telemetry": True}

# PostHog Project API key -- public write-only token, safe to embed
# (same one baked into the docs site's client bundle).
POSTHOG_TOKEN = os.environ.get(
    "NU_POSTHOG_TOKEN", "phc_yRpWfpoMeeRM8sKMPGPEsGy8ygNHJTpsGwrsikfpRfFz"
)
POSTHOG_HOST = os.environ.get("NU_POSTHOG_HOST", "https://t.nustack.dev").rstrip("/")
POSTHOG_CAPTURE_PATH = "/i/v0/e/"

FIRST_RUN_EVENT = "nu_first_run"

HTTP_TIMEOUT_SECONDS = 3
