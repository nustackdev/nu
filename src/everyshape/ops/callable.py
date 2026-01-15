"""Callable operations for function/method invocation and attribute access.

FuncCallOp, MethodCallOp: Call functions/methods with arguments
GetAttrOp, SetAttrOp, DelAttrOp: Attribute access operations

These enable custom typed values to integrate with the term system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyshape.term import Term

from .core import BinaryOp, NAryOp, TernaryOp


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.types import UnionBaseType


__all__ = [
    "DelAttrOp",
    "FuncCallOp",
    "GetAttrOp",
    "MethodCallOp",
    "SetAttrOp",
]


type OpArgument = Term | UnionBaseType


# =============================================================================
# FUNCTION CALL
# =============================================================================


class FuncCallOp[ResultT](NAryOp[ResultT]):
    """Call a function with arguments.

    Arguments can be raw values or Terms - Terms are executed before
    the function is called.

    Example:
        >>> FuncCallOp(datetime.now)
        >>> FuncCallOp(datetime, 2024, 1, 15)
    """

    def __init__(self, func: Callable[..., Any], *args: object, **kwargs: object) -> None:
        """Initialize function call operation.

        Args:
            func: The callable to invoke
            *args: Positional arguments (can be Terms or raw values)
            **kwargs: Keyword arguments (can be Terms or raw values)
        """
        self._func = func
        self._kwarg_keys = tuple(kwargs.keys())
        # Pass all args and kwargs values to base class
        super().__init__(*args, *kwargs.values())

    def _apply_op(self, *resolved: object) -> ResultT:
        """Apply the function call with resolved arguments."""
        # Split resolved args into positional and keyword
        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            args = resolved[:-num_kwargs]
            kwargs = dict(zip(self._kwarg_keys, resolved[-num_kwargs:], strict=True))
        else:
            args = resolved
            kwargs = {}
        return self._func(*args, **kwargs)

    def __repr__(self) -> str:
        """String representation."""
        func_name = getattr(self._func, "__name__", repr(self._func))
        args = ", ".join(repr(c) for c in self.children)
        return f"FuncCallOp({func_name}, {args})" if args else f"FuncCallOp({func_name})"


# =============================================================================
# METHOD CALL
# =============================================================================


class MethodCallOp[ResultT](NAryOp[ResultT]):
    """Call a method on an instance.

    The instance, method name, and arguments can be Terms - they are
    executed before the method is called.

    Example:
        >>> MethodCallOp(datetime_value, "timestamp")
        >>> MethodCallOp(datetime_value, "strftime", "%Y-%m-%d")
    """

    def __init__(
        self, instance: OpArgument, method_name: OpArgument, *args: object, **kwargs: object
    ) -> None:
        """Initialize method call operation.

        Args:
            instance: The instance to call the method on (can be Term or literal)
            method_name: Name of the method to call (can be Term or literal)
            *args: Positional arguments (can be Terms or raw values)
            **kwargs: Keyword arguments (can be Terms or raw values)
        """
        self._kwarg_keys = tuple(kwargs.keys())
        # Pass instance, method_name, args, and kwargs values to base class
        super().__init__(instance, method_name, *args, *kwargs.values())

    def _apply_op(self, *resolved: object) -> ResultT:
        """Apply the method call with resolved arguments."""
        instance = resolved[0]
        method_name = resolved[1]
        # Split remaining args into positional and keyword
        remaining = resolved[2:]
        num_kwargs = len(self._kwarg_keys)
        if num_kwargs:
            args = remaining[:-num_kwargs]
            kwargs = dict(zip(self._kwarg_keys, remaining[-num_kwargs:], strict=True))
        else:
            args = remaining
            kwargs = {}
        method = getattr(instance, str(method_name))
        return method(*args, **kwargs)

    def __repr__(self) -> str:
        """String representation."""
        args = ", ".join(repr(c) for c in self.children)
        return f"MethodCallOp({args})"


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttrOp[ResultT](BinaryOp[ResultT]):
    """Get an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute access.

    Example:
        >>> GetAttrOp(datetime_value, "year")
        >>> GetAttrOp(obj, attr_name_term)  # dynamic attribute
    """

    def _apply_op(self, instance: object, attr_name: object) -> ResultT:
        return getattr(instance, str(attr_name))


class SetAttrOp(TernaryOp[object]):
    """Set an attribute on an instance.

    All arguments can be Terms for dynamic attribute setting.

    Example:
        >>> SetAttrOp(obj, "name", "value")
    """

    def _apply_op(self, instance: object, attr_name: object, value: object) -> object:
        setattr(instance, str(attr_name), value)
        return value


class DelAttrOp(BinaryOp[None]):
    """Delete an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute deletion.

    Example:
        >>> DelAttrOp(obj, "cached_value")
    """

    def _apply_op(self, instance: object, attr_name: object) -> None:
        delattr(instance, str(attr_name))
