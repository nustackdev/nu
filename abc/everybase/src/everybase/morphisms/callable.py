"""Callable morphisms for function/method invocation and attribute access.

FuncCallOp, MethodCallOp: Call functions/methods with arguments
GetAttrOp, SetAttrOp, DelAttrOp: Attribute access operations

These enable custom typed values to integrate with the term system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyabc import BinaryMorphism, Command, NAryMorphism, Operation, TernaryMorphism


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "DelAttrOp",
    "FuncCallOp",
    "GetAttrOp",
    "MethodCallOp",
    "SetAttrOp",
]


# =============================================================================
# FUNCTION CALL
# =============================================================================


class FuncCallOp[ResultT](Operation, NAryMorphism[ResultT]):
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
        super().__init__(*args, *kwargs.values())
        self._func = func
        self._kwarg_keys = tuple(kwargs.keys())

    def apply(self, *resolved: object) -> ResultT:
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
        args = ", ".join(repr(c) for c in self._children)
        return f"FuncCallOp({func_name}, {args})" if args else f"FuncCallOp({func_name})"


# =============================================================================
# METHOD CALL
# =============================================================================


class MethodCallOp[ResultT](Operation, NAryMorphism[ResultT]):
    """Call a method on an instance.

    The instance, method name, and arguments can be Terms - they are
    executed before the method is called.

    Example:
        >>> MethodCallOp(datetime_value, "timestamp")
        >>> MethodCallOp(datetime_value, "strftime", "%Y-%m-%d")
    """

    def __init__(
        self, instance: object, method_name: object, *args: object, **kwargs: object
    ) -> None:
        """Initialize method call operation.

        Args:
            instance: The instance to call the method on (can be Term or literal)
            method_name: Name of the method to call (can be Term or literal)
            *args: Positional arguments (can be Terms or raw values)
            **kwargs: Keyword arguments (can be Terms or raw values)
        """
        super().__init__(instance, method_name, *args, *kwargs.values())
        self._kwarg_keys = tuple(kwargs.keys())

    def apply(self, *resolved: object) -> ResultT:
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
        args = ", ".join(repr(c) for c in self._children)
        return f"MethodCallOp({args})"


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttrOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Get an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute access.

    Example:
        >>> GetAttrOp(datetime_value, "year")
        >>> GetAttrOp(obj, attr_name_term)  # dynamic attribute
    """

    def apply(self, instance: object, attr_name: object) -> ResultT:
        """Apply."""
        return getattr(instance, str(attr_name))


class SetAttrOp(Command, TernaryMorphism[object]):
    """Set an attribute on an instance.

    All arguments can be Terms for dynamic attribute setting.
    This is a Command (impure) since it mutates state.

    Example:
        >>> SetAttrOp(obj, "name", "value")
    """

    def apply(self, instance: object, attr_name: object, value: object) -> object:
        """Apply."""
        setattr(instance, str(attr_name), value)
        return value


class DelAttrOp(Command, BinaryMorphism[None]):
    """Delete an attribute from an instance.

    Both instance and attr_name can be Terms for dynamic attribute deletion.
    This is a Command (impure) since it mutates state.

    Example:
        >>> DelAttrOp(obj, "cached_value")
    """

    def apply(self, instance: object, attr_name: object) -> None:
        """Apply."""
        delattr(instance, str(attr_name))
