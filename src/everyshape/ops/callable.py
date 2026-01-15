"""Callable operations for function/method invocation and attribute access.

FuncCallOp, MethodCallOp: Call functions/methods with arguments
GetAttrOp, SetAttrOp, DelAttrOp: Attribute access operations

These enable custom typed values to integrate with the term system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyshape.term import Term

from .core import NAryOp


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.term import Context
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
        self._args = args
        self._kwargs = kwargs

        # Collect Term children for dependency tracking
        children = []
        for arg in args:
            if isinstance(arg, Term):
                children.append(arg)
        for val in kwargs.values():
            if isinstance(val, Term):
                children.append(val)
        self.children = tuple(children)

    @property
    def is_pure(self) -> bool:
        """Function calls are pure if all arguments are pure."""
        for arg in self._args:
            if isinstance(arg, Term) and not arg.is_pure:
                return False
        for val in self._kwargs.values():
            if isinstance(val, Term) and not val.is_pure:
                return False
        return True

    def execute(self, context: Context) -> ResultT:
        """Execute the function call."""
        resolved_args = self._resolve_args(context, self._args)
        resolved_kwargs = self._resolve_kwargs(context, self._kwargs)
        return self._func(*resolved_args, **resolved_kwargs)

    def __repr__(self) -> str:
        """String representation."""
        func_name = getattr(self._func, "__name__", repr(self._func))
        args_repr = ", ".join(repr(a) for a in self._args)
        kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
        return f"FuncCallOp({func_name}, {all_args})" if all_args else f"FuncCallOp({func_name})"


# =============================================================================
# METHOD CALL
# =============================================================================


class MethodCallOp[ResultT](NAryOp[ResultT]):
    """Call a method on an instance.

    The instance and arguments can be Terms - they are executed before
    the method is called.

    Example:
        >>> MethodCallOp(datetime_value, "timestamp")
        >>> MethodCallOp(datetime_value, "strftime", "%Y-%m-%d")
    """

    def __init__(
        self, instance: OpArgument, method_name: str, *args: object, **kwargs: object
    ) -> None:
        """Initialize method call operation.

        Args:
            instance: The instance to call the method on (can be Term)
            method_name: Name of the method to call
            *args: Positional arguments (can be Terms or raw values)
            **kwargs: Keyword arguments (can be Terms or raw values)
        """
        self._instance = instance
        self._method_name = method_name
        self._args = args
        self._kwargs = kwargs

        # Collect Term children for dependency tracking
        children = [instance] if isinstance(instance, Term) else []
        for arg in args:
            if isinstance(arg, Term):
                children.append(arg)
        for val in kwargs.values():
            if isinstance(val, Term):
                children.append(val)
        self.children = tuple(children)

    @property
    def is_pure(self) -> bool:
        """Method calls are pure if all arguments are pure."""
        if isinstance(self._instance, Term) and not self._instance.is_pure:
            return False
        for arg in self._args:
            if isinstance(arg, Term) and not arg.is_pure:
                return False
        for val in self._kwargs.values():
            if isinstance(val, Term) and not val.is_pure:
                return False
        return True

    def execute(self, context: Context) -> ResultT:
        """Execute the method call."""
        # Resolve instance
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        resolved_args = self._resolve_args(context, self._args)
        resolved_kwargs = self._resolve_kwargs(context, self._kwargs)

        method = getattr(instance, self._method_name)
        return method(*resolved_args, **resolved_kwargs)

    def __repr__(self) -> str:
        """String representation."""
        args_repr = ", ".join(repr(a) for a in self._args)
        kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
        if all_args:
            return f"MethodCallOp({self._instance!r}, {self._method_name!r}, {all_args})"
        return f"MethodCallOp({self._instance!r}, {self._method_name!r})"


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================


class GetAttrOp[ResultT](NAryOp[ResultT]):
    """Get an attribute from an instance.

    Example:
        >>> GetAttrOp(datetime_value, "year")
    """

    def __init__(self, instance: OpArgument, attr_name: str) -> None:
        """Initialize get attribute operation.

        Args:
            instance: The instance to get the attribute from (can be Term)
            attr_name: Name of the attribute to get
        """
        self._instance = instance
        self._attr_name = attr_name
        self.children = (instance,) if isinstance(instance, Term) else ()

    @property
    def is_pure(self) -> bool:
        """Attribute access is pure if the instance is pure."""
        if isinstance(self._instance, Term):
            return self._instance.is_pure
        return True

    def execute(self, context: Context) -> ResultT:
        """Execute the attribute access."""
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance
        return getattr(instance, self._attr_name)

    def __repr__(self) -> str:
        """String representation."""
        return f"GetAttrOp({self._instance!r}, {self._attr_name!r})"


class SetAttrOp[ResultT](NAryOp[ResultT]):
    """Set an attribute on an instance.

    Example:
        >>> SetAttrOp(obj, "name", "value")
    """

    def __init__(self, instance: OpArgument, attr_name: str, value: object) -> None:
        """Initialize set attribute operation.

        Args:
            instance: The instance to set the attribute on (can be Term)
            attr_name: Name of the attribute to set
            value: Value to set (can be Term or raw value)
        """
        self._instance = instance
        self._attr_name = attr_name
        self._value = value

        children = []
        if isinstance(instance, Term):
            children.append(instance)
        if isinstance(value, Term):
            children.append(value)
        self.children = tuple(children)

    @property
    def is_pure(self) -> bool:
        """SetAttr is never pure as it mutates state."""
        return False

    def execute(self, context: Context) -> ResultT:
        """Execute the attribute set."""
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        if isinstance(self._value, Term):
            value = self._value.execute(context)
        else:
            value = self._value

        setattr(instance, self._attr_name, value)
        return value

    def __repr__(self) -> str:
        """String representation."""
        return f"SetAttrOp({self._instance!r}, {self._attr_name!r}, {self._value!r})"


class DelAttrOp(NAryOp[None]):
    """Delete an attribute from an instance.

    Example:
        >>> DelAttrOp(obj, "cached_value")
    """

    def __init__(self, instance: OpArgument, attr_name: str) -> None:
        """Initialize delete attribute operation.

        Args:
            instance: The instance to delete the attribute from (can be Term)
            attr_name: Name of the attribute to delete
        """
        self._instance = instance
        self._attr_name = attr_name
        self.children = (instance,) if isinstance(instance, Term) else ()

    @property
    def is_pure(self) -> bool:
        """DelAttr is never pure as it mutates state."""
        return False

    def execute(self, context: Context) -> None:
        """Execute the attribute deletion."""
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance
        delattr(instance, self._attr_name)

    def __repr__(self) -> str:
        """String representation."""
        return f"DelAttrOp({self._instance!r}, {self._attr_name!r})"
