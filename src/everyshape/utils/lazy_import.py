"""Lazy module loader with robust error handling and thread safety."""

from __future__ import annotations

import importlib
import sys
import threading
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from types import ModuleType


class LazyLoader:
    """Lazy-loading proxy for optional dependencies.

    Defers module import until first attribute access, enabling graceful
    handling of optional dependencies without import-time overhead.

    Thread-safe and preserves module identity after loading.
    """

    __slots__ = ("_error_hint", "_lock", "_module", "_name")

    def __init__(self, name: str, *, error_hint: str | None = None) -> None:
        """Initialize lazy loader.

        Args:
            name: Fully qualified module name (e.g., 'numpy', 'sklearn.metrics')
            error_hint: Custom installation message shown on ImportError
        """
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_module", None)
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_error_hint", error_hint)

    def _load(self) -> ModuleType:
        """Load the underlying module with thread-safe double-checked locking."""
        module = object.__getattribute__(self, "_module")
        if module is not None:
            return module

        lock = object.__getattribute__(self, "_lock")
        with lock:
            # Double-check after acquiring lock
            module = object.__getattribute__(self, "_module")
            if module is not None:
                return module

            name = object.__getattribute__(self, "_name")
            try:
                module = importlib.import_module(name)
            except ImportError as e:
                hint = object.__getattribute__(self, "_error_hint")
                msg = hint or (
                    f"Optional dependency '{name}' is not installed.\n"
                    f"Install it with: pip install {name.split('.')[0]}"
                )
                raise ImportError(msg) from e

            object.__setattr__(self, "_module", module)
            return module

    def __getattr__(self, name: str) -> object:
        """Delegate attribute access to the loaded module."""
        if name in {"_name", "_module", "_lock", "_error_hint"}:
            # Prevent infinite recursion on internal attributes
            return object.__getattribute__(self, name)
        return getattr(self._load(), name)

    def __setattr__(self, name: str, value: object) -> None:
        """Delegate attribute assignment to the loaded module."""
        setattr(self._load(), name, value)

    def __delattr__(self, name: str) -> None:
        """Delegate attribute deletion to the loaded module."""
        delattr(self._load(), name)

    def __dir__(self) -> list[str]:
        """Return combined attributes from proxy and loaded module."""
        module = object.__getattribute__(self, "_module")
        if module is None:
            return []
        return dir(module)

    def __repr__(self) -> str:
        """Show loader status without triggering import."""
        name = object.__getattribute__(self, "_name")
        module = object.__getattribute__(self, "_module")
        status = "loaded" if module is not None else "unloaded"
        return f"<LazyLoader({name!r}, status={status!r})>"

    def __getstate__(self) -> dict[str, Any]:
        """Support pickling by resetting to unloaded state."""
        return {
            "name": object.__getattribute__(self, "_name"),
            "error_hint": object.__getattribute__(self, "_error_hint"),
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore from pickle in unloaded state."""
        object.__setattr__(self, "_name", state["name"])
        object.__setattr__(self, "_error_hint", state.get("error_hint"))
        object.__setattr__(self, "_module", None)
        object.__setattr__(self, "_lock", threading.Lock())


def lazy_import(
    name: str,
    error_hint: str | None = None,
    install_to_sys_modules: bool = False,
) -> LazyLoader:
    """Create a lazy-loading proxy for an optional module.

    Args:
        name: Module name to import lazily
        error_hint: Custom error message for missing dependencies
        install_to_sys_modules: If True, register proxy in sys.modules
            to ensure module identity across imports

    Returns:
        LazyLoader proxy that imports on first access

    Example:
        >>> np = lazy_import("numpy", error_hint="Install: pip install numpy")
        >>> # numpy not imported yet
        >>> arr = np.array([1, 2, 3])  # imports numpy here
    """
    loader = LazyLoader(name, error_hint=error_hint)

    if install_to_sys_modules and name not in sys.modules:
        sys.modules[name] = cast("ModuleType", loader)

    return loader


__all__ = ["LazyLoader", "lazy_import"]
