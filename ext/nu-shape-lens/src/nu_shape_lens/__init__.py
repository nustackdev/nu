"""eb-shape-lens: Terminal data viewer for everybase Shapes."""

from __future__ import annotations

from .render import render


__all__ = [
    "format_shape",
    "print_shape",
]


def _normalize(storage: object) -> object:
    """Normalize storage to a renderer-friendly form.

    Accepts:
      - ``None`` → returns ``None`` (shows empty)
      - ``dict`` → pass through
      - PV view (has ``container`` + ``open_child``) → pass through (lazy)
      - Other with ``.extract()`` → call extract, return dict
    """
    if storage is None:
        return None
    if isinstance(storage, dict):
        return storage
    # PV views: pass through for lazy field-by-field access
    if hasattr(storage, "container") and hasattr(storage, "open_child"):
        return storage
    # Generic views: extract to dict
    if hasattr(storage, "extract"):
        data = storage.extract()  # type: ignore[union-attr]
        return data if isinstance(data, dict) else None
    return None


def format_shape(
    shape_cls: type,
    storage: object = None,
    *,
    color: bool = True,
    max_items: int = 20,
    max_depth: int = 10,
    max_str: int = 80,
) -> str:
    """Format shape storage data as an ANSI-colored tree.

    Args:
        shape_cls: Shape class (has ``_slots`` with typed slot definitions).
        storage: Backing storage — a plain dict, or a PV view (lazy access).
        color: Emit ANSI escape codes.
        max_items: Max collection items before truncation.
        max_depth: Max nesting depth.
        max_str: Max string value length before truncation.

    Returns:
        Multi-line string.
    """
    data = _normalize(storage)
    return render(
        shape_cls,
        data,
        color=color,
        max_items=max_items,
        max_depth=max_depth,
        max_str=max_str,
    )


def print_shape(
    shape_cls: type,
    storage: object = None,
    *,
    color: bool = True,
    max_items: int = 20,
    max_depth: int = 10,
    max_str: int = 80,
) -> None:
    """Print shape storage data as an ANSI-colored tree."""
    print(  # noqa: T201
        format_shape(
            shape_cls,
            storage,
            color=color,
            max_items=max_items,
            max_depth=max_depth,
            max_str=max_str,
        )
    )
