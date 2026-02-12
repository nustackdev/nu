"""Shape data -> ANSI tree rendering.

Walks Shape._slots to discover field names and ref types,
then renders the corresponding data from the backing storage.

Accepts both plain dicts (dict substrate) and PV views (lazy iteration).

Classification is duck-typed via slot.ref_cls name and slot.kwargs,
so no substrate imports are needed. Slot type annotations are shown
inline so you always know the declared type next to the actual value.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from itertools import islice
from typing import Any


# ── ANSI codes ────────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

# ── Box-drawing ───────────────────────────────────────────────────────────────

_BRANCH = "\u251c\u2500\u2500"  # ├──
_LAST = "\u2514\u2500\u2500"  # └──
_PIPE = "\u2502  "  # │
_SPACE = "   "

# ── Defaults ──────────────────────────────────────────────────────────────────

MAX_ITEMS = 20
MAX_DEPTH = 10
MAX_STR = 80

# Duck-typed alias
_Any = Any


# ── Helpers ───────────────────────────────────────────────────────────────────


def _dim(text: str, c: bool) -> str:
    return f"{DIM}{text}{RESET}" if c else text


def _conn(is_last: bool, c: bool) -> str:
    return _dim(_LAST if is_last else _BRANCH, c)


def _cpfx(prefix: str, is_last: bool, c: bool) -> str:
    return prefix + (_SPACE if is_last else _dim(_PIPE, c))


def _colon(c: bool) -> str:
    return _dim(":", c)


def _shape_hdr(cls: _Any, c: bool) -> str:
    name = cls.__name__
    return f"{BOLD}{MAGENTA}{name}{RESET}" if c else name


def _fname(name: str, c: bool) -> str:
    return f"{BOLD}{name}{RESET}" if c else name


def _kstr(key: object, c: bool) -> str:
    t = repr(key)
    return f"{YELLOW}{t}{RESET}" if c else t


def _istr(idx: int, c: bool) -> str:
    return _dim(f"[{idx}]", c)


def _type_tag(slot: _Any, c: bool) -> str:
    """Build a dim type annotation from slot metadata, e.g. 'int' or 'dict[str, float]'."""
    ref_name = slot.ref_cls.__name__
    kw = slot.kwargs

    # Strip substrate prefix and "Ref" suffix to get a human-friendly type name.
    # e.g. "IntRef" -> "int", "FloatRef" -> "float", "MappingRef" -> "dict"
    short = ref_name
    for prefix in ("Mutable", "Reactive"):
        if short.startswith(prefix):
            short = short[len(prefix) :]

    # Map common ref names to Python type names
    _type_map: dict[str, str] = {
        "IntRef": "int",
        "FloatRef": "float",
        "StrRef": "str",
        "BoolRef": "bool",
        "BytesRef": "bytes",
        "DecimalRef": "Decimal",
        "DatetimeRef": "datetime",
        "TimedeltaRef": "timedelta",
        "UUIDRef": "UUID",
        "PathRef": "Path",
        "PercentageRef": "Percentage",
        "BasisPointRef": "BasisPoint",
        "ItemRef": "item",
    }

    fallback = short.removesuffix("Ref").lower() if short.endswith("Ref") else short
    base = _type_map.get(short) or fallback

    # Enrich with kwargs
    shape_type = kw.get("shape_type")
    value_type = kw.get("value_type")
    item_type = kw.get("item_type")
    key_type = kw.get("key_type")

    if shape_type is not None:
        sname = shape_type.__name__
        if "Dict" in ref_name or "Mapping" in ref_name:
            kt = key_type.__name__ if key_type else "str"
            tag = f"dict[{kt}, {sname}]"
        elif "List" in ref_name or "Sequence" in ref_name:
            tag = f"list[{sname}]"
        else:
            tag = sname
    elif "Dict" in ref_name or "Mapping" in ref_name:
        kt = key_type.__name__ if key_type else "str"
        vt = value_type.__name__ if value_type else "object"
        tag = f"dict[{kt}, {vt}]"
    elif "List" in ref_name or "Sequence" in ref_name:
        it = item_type.__name__ if item_type else "object"
        tag = f"list[{it}]"
    elif "Set" in ref_name:
        it = item_type.__name__ if item_type else "object"
        tag = f"set[{it}]"
    else:
        tag = base

    return _dim(tag, c)


# ── Slot classification ──────────────────────────────────────────────────────


def _classify(slot: _Any) -> str:
    """Classify slot -> 'scalar'|'dict'|'list'|'set'|'shape'|'shapes_dict'|'shapes_list'."""
    name = slot.ref_cls.__name__
    has_shape = "shape_type" in slot.kwargs

    if has_shape:
        if "Dict" in name or "Mapping" in name:
            return "shapes_dict"
        if "List" in name or "Sequence" in name:
            return "shapes_list"
        return "shape"

    if "Dict" in name or "Mapping" in name:
        return "dict"
    if "List" in name or "Sequence" in name:
        return "list"
    if "Set" in name:
        return "set"
    return "scalar"


# ── Lazy view helpers ────────────────────────────────────────────────────────


def _is_view(data: object) -> bool:
    """Check if data is a PV view (has container + open_child)."""
    return hasattr(data, "container") and hasattr(data, "open_child")


def _find_list_view(view: object) -> type | None:
    """Discover ListView class from a view's module package."""
    mod_name = type(view).__module__
    pkg_name = mod_name.rsplit(".", 1)[0] if "." in mod_name else mod_name
    pkg = sys.modules.get(pkg_name)
    return getattr(pkg, "ListView", None) if pkg else None  # type: ignore[return-value]


def _view_child(data: object, name: str, kind: str) -> object:
    """Get a field value from a PV view, lazily when possible.

    - Scalar fields: reads primitive directly from container (instant).
    - Container fields: opens a child view (lazy, no full extraction).
    """
    try:
        ct = data.container.get_child_type(name)  # type: ignore[union-attr]
    except Exception:
        return None

    # Primitive child → instant read
    if ct.name == "PRIMITIVE":
        try:
            return data.container.get_child_primitive(name)  # type: ignore[union-attr]
        except Exception:
            return None

    # Container child → open as lazy view
    try:
        if kind in ("list", "shapes_list"):
            list_cls = _find_list_view(data)
            if list_cls is not None:
                return data.open_child(name, list_cls)  # type: ignore[union-attr]
        return data.open_child(name, type(data))  # type: ignore[union-attr]
    except Exception:
        return None


def _get_field(data: object, name: str, kind: str) -> object:
    """Get a field value from data (dict or view), lazily for views."""
    if data is None:
        return None
    if isinstance(data, dict):
        return data.get(name)
    if _is_view(data):
        return _view_child(data, name, kind)
    # Generic Mapping fallback
    if isinstance(data, Mapping):
        try:
            return data[name]
        except (KeyError, IndexError):
            return None
    return None


# ── Type checks (dict + views) ──────────────────────────────────────────────


def _is_mapping(data: object) -> bool:
    """Check if data is a dict-like mapping (dict or Mapping view)."""
    return isinstance(data, Mapping)


def _is_sequence(data: object) -> bool:
    """Check if data is a list-like sequence (list or Sequence view, not str/bytes)."""
    return isinstance(data, Sequence) and not isinstance(data, (str, bytes))


def _safe_len(data: object, batch_count: int) -> int | None:
    """Get collection length, or ``None`` if the true size is unknown.

    Returns the real length when ``len(data)`` is trustworthy (≥ *batch_count*).
    When metadata is stale (PV views populated via child ops) or ``len()`` is
    unavailable, returns ``None`` so callers can show "N+ items" instead of a
    wrong number.
    """
    try:
        n = len(data)  # type: ignore[arg-type]
        if n >= batch_count:
            return n
    except TypeError:
        pass
    return None


# ── Value formatting ─────────────────────────────────────────────────────────


def _fval(value: object, c: bool, ms: int) -> str:
    """Format a scalar value with optional ANSI."""
    if value is None:
        return _dim("\u2205", c)  # ∅

    if isinstance(value, bool):
        t = str(value).lower()
        return f"{YELLOW}{t}{RESET}" if c else t

    if isinstance(value, (int, float)):
        t = repr(value)
        return f"{CYAN}{t}{RESET}" if c else t

    if isinstance(value, str):
        v = value if len(value) <= ms else value[: ms - 3] + "..."
        t = repr(v)
        return f"{GREEN}{t}{RESET}" if c else t

    t = repr(value)
    if len(t) > ms:
        t = t[: ms - 3] + "..."
    return t


# ── Public entry ──────────────────────────────────────────────────────────────


def render(
    shape_cls: _Any,
    data: object,
    *,
    color: bool = True,
    max_items: int = MAX_ITEMS,
    max_depth: int = MAX_DEPTH,
    max_str: int = MAX_STR,
) -> str:
    """Render shape data as a tree string."""
    lines: list[str] = []
    lines.append(_shape_hdr(shape_cls, color))
    _slots(shape_cls, data, lines, "", 0, color, max_items, max_depth, max_str)
    return "\n".join(lines)


# ── Slot iteration ────────────────────────────────────────────────────────────


def _slots(
    shape_cls: _Any,
    data: object,
    lines: list[str],
    prefix: str,
    depth: int,
    c: bool,
    mi: int,
    md: int,
    ms: int,
) -> None:
    """Render all slots of a shape."""
    if depth >= md:
        lines.append(f"{prefix}{_conn(True, c)} {_dim('... (max depth)', c)}")
        return

    slot_map: dict[str, _Any] = getattr(shape_cls, "_slots", {})
    items = list(slot_map.items())

    for i, (name, slot) in enumerate(items):
        il = i == len(items) - 1
        kind = _classify(slot)
        fd = _get_field(data, name, kind)
        _field(name, kind, slot, fd, lines, prefix, il, depth, c, mi, md, ms)


# ── Field rendering ──────────────────────────────────────────────────────────


def _field(
    name: str,
    kind: str,
    slot: _Any,
    data: object,
    lines: list[str],
    prefix: str,
    il: bool,
    depth: int,
    c: bool,
    mi: int,
    md: int,
    ms: int,
) -> None:
    """Render a single field."""
    cn = _conn(il, c)
    fn = _fname(name, c)
    co = _colon(c)
    cp = _cpfx(prefix, il, c)
    tt = _type_tag(slot, c)

    if kind == "scalar":
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_fval(data, c, ms)}")

    elif kind == "dict":
        _prim_dict(fn, tt, data, lines, prefix, cn, co, cp, c, mi, ms)

    elif kind == "list":
        _prim_list(fn, tt, data, lines, prefix, cn, co, cp, c, mi, ms)

    elif kind == "set":
        _prim_set(fn, tt, data, lines, prefix, cn, co, cp, c, ms)

    elif kind == "shape":
        st = slot.kwargs.get("shape_type")
        if not _is_mapping(data) or st is None:
            lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('\u2205', c)}")
        else:
            lines.append(f"{prefix}{cn} {fn}{co} {_shape_hdr(st, c)}")
            _slots(st, data, lines, cp, depth + 1, c, mi, md, ms)

    elif kind == "shapes_dict":
        st = slot.kwargs.get("shape_type")
        _sh_dict(fn, tt, st, data, lines, prefix, cn, co, cp, depth, c, mi, md, ms)

    elif kind == "shapes_list":
        st = slot.kwargs.get("shape_type")
        _sh_list(fn, tt, st, data, lines, prefix, cn, co, cp, depth, c, mi, md, ms)


# ── Primitive collections ─────────────────────────────────────────────────────


def _prim_dict(
    fn: str,
    tt: str,
    data: object,
    lines: list[str],
    prefix: str,
    cn: str,
    co: str,
    cp: str,
    c: bool,
    mi: int,
    ms: int,
) -> None:
    if not _is_mapping(data):
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{}', c)}")
        return

    # Materialize bounded batch (lazy — touches at most mi+1 items)
    batch = list(islice(data.items(), mi + 1))  # type: ignore[union-attr]
    if not batch:
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{}', c)}")
        return

    n = _safe_len(data, len(batch))
    shown = min(len(batch), mi)
    has_more = len(batch) > mi
    if n is not None and n <= 5:
        pairs = [f"{_kstr(k, c)}: {_fval(v, c, ms)}" for k, v in batch[:5]]
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{', c)}{', '.join(pairs)}{_dim('}', c)}")
    else:
        cnt = f"{n} items" if n is not None else f"{shown}+ items"
        lines.append(f"{prefix}{cn} {fn} {tt} {_dim(f'({cnt})', c)}")
        for j, (k, v) in enumerate(batch[:mi]):
            jl = j == shown - 1 and not has_more
            lines.append(f"{cp}{_conn(jl, c)} {_kstr(k, c)}: {_fval(v, c, ms)}")
        if has_more:
            tail = f"... and {n - mi} more" if n is not None else "..."
            lines.append(f"{cp}{_conn(True, c)} {_dim(tail, c)}")


def _prim_list(
    fn: str,
    tt: str,
    data: object,
    lines: list[str],
    prefix: str,
    cn: str,
    co: str,
    cp: str,
    c: bool,
    mi: int,
    ms: int,
) -> None:
    if not _is_sequence(data):
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('[]', c)}")
        return

    batch = list(islice(data, mi + 1))  # type: ignore[arg-type]
    if not batch:
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('[]', c)}")
        return

    n = _safe_len(data, len(batch))
    shown = min(len(batch), mi)
    has_more = len(batch) > mi
    if n is not None and n <= 5:
        vals = [_fval(v, c, ms) for v in batch[:5]]
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('[', c)}{', '.join(vals)}{_dim(']', c)}")
    else:
        cnt = f"{n} items" if n is not None else f"{shown}+ items"
        lines.append(f"{prefix}{cn} {fn} {tt} {_dim(f'({cnt})', c)}")
        for j, v in enumerate(batch[:mi]):
            jl = j == shown - 1 and not has_more
            lines.append(f"{cp}{_conn(jl, c)} {_istr(j, c)} {_fval(v, c, ms)}")
        if has_more:
            tail = f"... and {n - mi} more" if n is not None else "..."
            lines.append(f"{cp}{_conn(True, c)} {_dim(tail, c)}")


def _prim_set(
    fn: str,
    tt: str,
    data: object,
    lines: list[str],
    prefix: str,
    cn: str,
    co: str,
    cp: str,
    c: bool,
    ms: int,
) -> None:
    if not data or not isinstance(data, (set, frozenset)):
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('set()', c)}")
        return

    vals = [_fval(v, c, ms) for v in sorted(data, key=repr)]
    if len(vals) <= 5:
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{', c)}{', '.join(vals)}{_dim('}', c)}")
    else:
        head = ", ".join(vals[:5])
        lines.append(
            f"{prefix}{cn} {fn} {tt}{co} {_dim('{', c)}{head}, {_dim(f'... +{len(vals) - 5}', c)}{_dim('}', c)}"
        )


# ── Shape collections ─────────────────────────────────────────────────────────


def _sh_dict(
    fn: str,
    tt: str,
    st: _Any,
    data: object,
    lines: list[str],
    prefix: str,
    cn: str,
    co: str,
    cp: str,
    depth: int,
    c: bool,
    mi: int,
    md: int,
    ms: int,
) -> None:
    if not _is_mapping(data):
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{}', c)}")
        return

    batch = list(islice(data.items(), mi + 1))  # type: ignore[union-attr]
    if not batch:
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('{}', c)}")
        return

    n = _safe_len(data, len(batch))
    shown = min(len(batch), mi)
    has_more = len(batch) > mi
    cnt = f"{n} items" if n is not None else f"{shown}+ items"
    lines.append(f"{prefix}{cn} {fn} {tt} {_dim(f'({cnt})', c)}")
    for j, (k, v) in enumerate(batch[:mi]):
        jl = j == shown - 1 and not has_more
        hdr = f"{_kstr(k, c)}{_colon(c)} {_shape_hdr(st, c)}"
        lines.append(f"{cp}{_conn(jl, c)} {hdr}")
        icp = _cpfx(cp, jl, c)
        _slots(st, v if _is_mapping(v) else None, lines, icp, depth + 1, c, mi, md, ms)
    if has_more:
        tail = f"... and {n - mi} more" if n is not None else "..."
        lines.append(f"{cp}{_conn(True, c)} {_dim(tail, c)}")


def _sh_list(
    fn: str,
    tt: str,
    st: _Any,
    data: object,
    lines: list[str],
    prefix: str,
    cn: str,
    co: str,
    cp: str,
    depth: int,
    c: bool,
    mi: int,
    md: int,
    ms: int,
) -> None:
    if not _is_sequence(data):
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('[]', c)}")
        return

    batch = list(islice(data, mi + 1))  # type: ignore[arg-type]
    if not batch:
        lines.append(f"{prefix}{cn} {fn} {tt}{co} {_dim('[]', c)}")
        return

    n = _safe_len(data, len(batch))
    shown = min(len(batch), mi)
    has_more = len(batch) > mi
    cnt = f"{n} items" if n is not None else f"{shown}+ items"
    lines.append(f"{prefix}{cn} {fn} {tt} {_dim(f'({cnt})', c)}")
    for j, v in enumerate(batch[:mi]):
        jl = j == shown - 1 and not has_more
        hdr = f"{_istr(j, c)} {_shape_hdr(st, c)}"
        lines.append(f"{cp}{_conn(jl, c)} {hdr}")
        icp = _cpfx(cp, jl, c)
        _slots(st, v if _is_mapping(v) else None, lines, icp, depth + 1, c, mi, md, ms)
    if has_more:
        tail = f"... and {n - mi} more" if n is not None else "..."
        lines.append(f"{cp}{_conn(True, c)} {_dim(tail, c)}")
