"""Operations for TypedValue/TypedVar support.

This module provides operations for working with custom typed values:

Operations:
    - FuncCallOp: Call a function with arguments (for constructors)
    - MethodCallOp: Call an instance method (for value methods)
    - GetAttrOp: Get an attribute from an instance
    - SetAttrOp: Set an attribute on an instance
    - DelAttrOp: Delete an attribute from an instance

Commands:
    - TypedSetCmd: Set command that calls __to_storage__ before storing

These enable users to create custom typed values like DatetimeValue
that integrate with the term/command system.

Example:
    >>> class DatetimeValue(TypedValue[datetime]):
    ...     @classmethod
    ...     def now(cls) -> DatetimeValue:
    ...         return DatetimeValue(FuncCallOp(datetime.now))
    ...
    ...     def timestamp(self) -> FloatType:
    ...         return FloatType(MethodCallOp(self, "timestamp"))
    ...
    ...     def __to_storage__(self) -> float:
    ...         return self.execute(ctx).timestamp()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from everyshape.loc import path
from everyshape.typing import Sentinel
from everyshape.view import Assignable

from ..term import Command, Operation, PrimitiveRef, Term


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..context import Context
    from ..refs import UnionRefBases
    from ..types.bases import UnionBaseType


__all__ = [
    "DelAttrOp",
    "FuncCallOp",
    "GetAttrOp",
    "MethodCallOp",
    "SetAttrOp",
    "TypedSetCmd",
]


type OpArgument = Term | UnionBaseType


# =============================================================================
# FUNCTION CALL OPERATION
# =============================================================================


class FuncCallOp[ResultT](Operation[ResultT]):
    """Operation that calls a function/method with arguments.

    FuncCallOp enables calling arbitrary callables within the term system.
    Arguments can be raw values or Terms - Terms are executed before
    the function is called.

    This is primarily used for creating TypedValue constructors, allowing
    users to define custom typed values with method-based construction.

    Type Parameters:
        ResultT: The return type of the function

    Example:
        >>> # Direct function call
        >>> FuncCallOp(datetime.now)
        >>> FuncCallOp(datetime, 2024, 1, 15)

        >>> # Used in TypedValue subclass
        >>> class DatetimeValue(TypedValue[datetime]):
        ...     @classmethod
        ...     def now(cls) -> DatetimeValue:
        ...         return DatetimeValue(FuncCallOp(datetime.now))
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
        """Function calls are pure if all arguments are pure.

        Note: We cannot know if the function itself is pure,
        so we assume it is if all inputs are pure.

        Returns:
            True if all Term arguments are pure
        """
        for arg in self._args:
            if isinstance(arg, Term) and not arg.is_pure:
                return False
        for val in self._kwargs.values():
            if isinstance(val, Term) and not val.is_pure:
                return False
        return True

    def execute(self, context: Context) -> ResultT:
        """Execute the function call.

        Resolves all Term arguments by executing them, then calls
        the function with the resolved values.

        Args:
            context: Execution context

        Returns:
            The function's return value
        """
        # Resolve positional arguments
        resolved_args = []
        for arg in self._args:
            if isinstance(arg, Term):
                resolved_args.append(arg.execute(context))
            else:
                resolved_args.append(arg)

        # Resolve keyword arguments
        resolved_kwargs = {}
        for key, val in self._kwargs.items():
            if isinstance(val, Term):
                resolved_kwargs[key] = val.execute(context)
            else:
                resolved_kwargs[key] = val

        return self._func(*resolved_args, **resolved_kwargs)

    def __repr__(self) -> str:
        """String representation."""
        func_name = getattr(self._func, "__name__", repr(self._func))
        args_repr = ", ".join(repr(a) for a in self._args)
        kwargs_repr = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        all_args = ", ".join(filter(None, [args_repr, kwargs_repr]))
        return f"FuncCallOp({func_name}, {all_args})" if all_args else f"FuncCallOp({func_name})"


# =============================================================================
# METHOD CALL OPERATION
# =============================================================================


class MethodCallOp[ResultT](Operation[ResultT]):
    """Operation that calls a method on an instance.

    MethodCallOp enables calling instance methods within the term system.
    The instance and arguments can be Terms - they are executed before
    the method is called.

    This is used for calling methods on TypedValue's underlying value,
    e.g. calling datetime.timestamp() on a DatetimeValue.

    Type Parameters:
        ResultT: The return type of the method

    Example:
        >>> # Call datetime.timestamp() method
        >>> MethodCallOp(datetime_value, "timestamp")

        >>> # Call with arguments
        >>> MethodCallOp(datetime_value, "strftime", "%Y-%m-%d")

        >>> # Used in TypedValue subclass
        >>> class DatetimeValue(TypedValue[datetime]):
        ...     def timestamp(self) -> FloatType:
        ...         return FloatType(MethodCallOp(self, "timestamp"))
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
        """Method calls are pure if all arguments are pure.

        Note: We cannot know if the method itself is pure,
        so we assume it is if all inputs are pure.

        Returns:
            True if all Term arguments are pure
        """
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
        """Execute the method call.

        Resolves the instance and all Term arguments by executing them,
        then calls the method with the resolved values.

        Args:
            context: Execution context

        Returns:
            The method's return value
        """
        # Resolve instance
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        # Resolve positional arguments
        resolved_args = []
        for arg in self._args:
            if isinstance(arg, Term):
                resolved_args.append(arg.execute(context))
            else:
                resolved_args.append(arg)

        # Resolve keyword arguments
        resolved_kwargs = {}
        for key, val in self._kwargs.items():
            if isinstance(val, Term):
                resolved_kwargs[key] = val.execute(context)
            else:
                resolved_kwargs[key] = val

        # Get and call the method
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
# ATTRIBUTE OPERATIONS
# =============================================================================


class GetAttrOp[ResultT](Operation[ResultT]):
    """Operation that gets an attribute from an instance.

    GetAttrOp enables getting instance attributes within the term system.
    The instance can be an Term - it is executed before the attribute
    is retrieved.

    Type Parameters:
        ResultT: The type of the attribute value

    Example:
        >>> # Get datetime.year attribute
        >>> GetAttrOp(datetime_value, "year")

        >>> # Used in TypedValue subclass
        >>> class DatetimeValue(TypedValue[datetime]):
        ...     @property
        ...     def year(self) -> IntType:
        ...         return IntType(GetAttrOp(self, "year"))
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
        """Attribute access is pure if the instance is pure.

        Returns:
            True if the instance is pure
        """
        if isinstance(self._instance, Term):
            return self._instance.is_pure
        return True

    def execute(self, context: Context) -> ResultT:
        """Execute the attribute access.

        Args:
            context: Execution context

        Returns:
            The attribute value
        """
        # Resolve instance
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        return getattr(instance, self._attr_name)

    def __repr__(self) -> str:
        """String representation."""
        return f"GetAttrOp({self._instance!r}, {self._attr_name!r})"


class SetAttrOp[ResultT](Operation[ResultT]):
    """Operation that sets an attribute on an instance.

    SetAttrOp enables setting instance attributes within the term system.
    The instance and value can be Terms - they are executed before
    the attribute is set.

    Type Parameters:
        ResultT: The type of the value being set

    Example:
        >>> # Set an attribute
        >>> SetAttrOp(obj, "name", "value")

        >>> # With Term
        >>> SetAttrOp(obj_ref, "count", count_ref)
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

        # Collect Term children for dependency tracking
        children = []
        if isinstance(instance, Term):
            children.append(instance)
        if isinstance(value, Term):
            children.append(value)
        self.children = tuple(children)

    @property
    def is_pure(self) -> bool:
        """SetAttr is never pure as it mutates state.

        Returns:
            Always False
        """
        return False

    def execute(self, context: Context) -> ResultT:
        """Execute the attribute set.

        Args:
            context: Execution context

        Returns:
            The value that was set
        """
        # Resolve instance
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        # Resolve value
        if isinstance(self._value, Term):
            value = self._value.execute(context)
        else:
            value = self._value

        setattr(instance, self._attr_name, value)
        return value

    def __repr__(self) -> str:
        """String representation."""
        return f"SetAttrOp({self._instance!r}, {self._attr_name!r}, {self._value!r})"


class DelAttrOp(Operation[None]):
    """Operation that deletes an attribute from an instance.

    DelAttrOp enables deleting instance attributes within the term system.
    The instance can be an Term - it is executed before the attribute
    is deleted.

    Example:
        >>> # Delete an attribute
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
        """DelAttr is never pure as it mutates state.

        Returns:
            Always False
        """
        return False

    def execute(self, context: Context) -> None:
        """Execute the attribute deletion.

        Args:
            context: Execution context

        Returns:
            None
        """
        # Resolve instance
        if isinstance(self._instance, Term):
            instance = self._instance.execute(context)
        else:
            instance = self._instance

        delattr(instance, self._attr_name)

    def __repr__(self) -> str:
        """String representation."""
        return f"DelAttrOp({self._instance!r}, {self._attr_name!r})"


# =============================================================================
# TYPED SET COMMAND
# =============================================================================


class TypedSetCmd[T](Command[T]):
    """Set command for TypedValue that calls __to_storage__ before storing.

    Like SetCmd, but before writing to storage, it checks if the value
    has a __to_storage__ method and calls it to convert the typed value
    to a storable format.

    This enables custom types like DatetimeValue to define how they
    should be serialized to storage.

    Type Parameters:
        T: Type of value to write (the storage type)

    Example:
        >>> class DatetimeValue(TypedValue[datetime]):
        ...     def __to_storage__(self) -> float:
        ...         # Store as Unix timestamp
        ...         return self._value.timestamp()
        >>> typed_set = TypedSetCmd(ref, datetime_value)
        >>> typed_set.execute(ctx)  # Stores the timestamp float
    """

    def __init__(
        self,
        ref: PrimitiveRef[T] | UnionRefBases,
        value: Term[T | Sentinel],
    ) -> None:
        """Initialize typed set command.

        Args:
            ref: Reference to write to
            value: Value to write (can be TypedValue with __to_storage__)
        """
        self.ref = cast("PrimitiveRef[T]", ref)
        self.value_expr = value
        self.children = (cast("PrimitiveRef[T]", ref), value)

    def execute(self, context: Context) -> T:
        """Execute typed write command.

        If the value has __to_storage__, calls it to get the storable value.
        Otherwise stores the value directly.

        Args:
            context: Execution context with transaction

        Returns:
            The written value (after __to_storage__ conversion if applicable)
        """
        # Resolve ref to Path
        value_path = self.ref.resolve(context)

        # Evaluate value expression
        value = self.value_expr.execute(context)

        if isinstance(value, Sentinel):
            raise ValueError(f"Cannot store special values (Empty, NaN, etc): {value}")

        # Check for __to_storage__ method and call it if present
        if hasattr(value, "__to_storage__"):
            storage_value = value.__to_storage__()
        else:
            storage_value = value

        # Get root view from context
        root_view = context.get_context_for_shape(self.ref.get_root_shape()).root_view

        # Navigate using Path system
        parent_view, key = path.navigate_value(root_view, value_path)

        # Store through view
        if not isinstance(parent_view, Assignable):
            raise TypeError(
                f"View {parent_view.__class__.__name__} does not implement Assignable protocol."
            )

        # Write value
        parent_view[key] = storage_value
        return storage_value

    def __repr__(self) -> str:
        return f"TypedSetCmd({self.ref!r}, {self.value_expr!r})"
