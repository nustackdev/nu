"""Story fixtures: what Python sends, written where the kit's Storybook reads it.

A story that draws a ref from a hand-written copy of its props drifts the
day the builder changes. These fixtures are the builder's own output instead,
checked on every test run: a test renders what it covers, and
:func:`check_fixture` compares it with the file the stories import. With
``UPDATE_STORY_FIXTURES=1`` (or a test's own older flag) it writes the file
first, so a change to a builder is one command away from the stories.

    UPDATE_STORY_FIXTURES=1 uv run pytest tests/nustd/ui/test_chart.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


__all__ = ["STORIES", "check_fixture", "frame_json"]


#: The kit's stories directory.
STORIES = Path(__file__).resolve().parents[3] / "pkgs/ts/ui-kit/src/stories"

#: The env flag every fixture test honors.
FLAG = "UPDATE_STORY_FIXTURES"


def frame_json(frame: Any) -> dict[str, Any]:
    """One wire frame as the browser's tree store takes it: ``{op, ref, payload?, chain}``."""
    out: dict[str, Any] = {"op": frame.op, "ref": list(frame.ref)}
    if frame.payload is not None:
        out["payload"] = frame.payload
    out["chain"] = [[seg, typ, props] for seg, typ, props in frame.chain]
    return json.loads(json.dumps(out))


def _dumps(value: Any, depth: int = 0) -> str:
    """JSON with tab indents, a list with no objects in it on one line when it fits.

    The layout the kit's formatter gives these files, so writing one leaves
    a diff of what changed and nothing else.
    """
    pad = "\t" * depth
    if isinstance(value, list) and value and "{" not in (flat := json.dumps(value)):
        # A tab counts 2 and a line runs to 100, the way the formatter measures.
        if len(pad) * 2 + len(flat) <= 100:
            return flat
    if isinstance(value, list) and value:
        items = ",\n".join(pad + "\t" + _dumps(v, depth + 1) for v in value)
        return f"[\n{items}\n{pad}]"
    if isinstance(value, dict) and value:
        items = ",\n".join(
            f"{pad}\t{json.dumps(k)}: {_dumps(v, depth + 1)}" for k, v in value.items()
        )
        return f"{{\n{items}\n{pad}}}"
    return json.dumps(value)


def check_fixture(path: Path, current: Any, *, test: str, flags: tuple[str, ...] = ()) -> None:
    """Fail unless ``path`` holds ``current``; write it first under the update flag.

    Args:
        current: plain JSON data, already round-tripped, so tuples compare as lists.
        test: the test file to name in the failure, the one to rerun.
        flags: older env flags that update this fixture too.
    """
    if any(os.environ.get(f) for f in (FLAG, *flags)):
        path.write_text(_dumps(current) + "\n")
    hint = f"{FLAG}=1 uv run pytest {test}"
    assert path.exists(), f"no story fixture at {path.name}: {hint}"
    assert json.loads(path.read_text()) == current, f"{path.name} drifted from Python: {hint}"
