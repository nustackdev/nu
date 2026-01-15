"""Base class for N-ary operations.

N-ary operations have variable numbers of arguments, used for:
- Function calls: FuncCallOp, MethodCallOp
- Operations with optional parameters: MapOp, FilterOp, ReduceOp
- Attribute access: GetAttrOp, SetAttrOp, DelAttrOp
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from everyshape.term import Operation, Term


if TYPE_CHECKING:
    from everyshape.term import Context

__all__ = ["NAryOp"]


class NAryOp[ResultT](Operation[ResultT]):
    """Base class for N-ary operations (variable arguments).

    N-ary operations handle variable numbers of arguments, supporting
    both positional and keyword arguments. Arguments can be Terms
    (executed during evaluation) or raw values (passed directly).

    Children tracking collects all Term arguments for dependency analysis
    and purity checking.

    Subclasses implement `execute()` with their specific argument handling.

    Example:
        class FuncCallOp(NAryOp[ResultT]):
            def __init__(self, func: Callable, *args, **kwargs):
                self._func = func
                self._args = args
                self._kwargs = kwargs
                # Collect Term children
                children = [a for a in args if isinstance(a, Term)]
                children.extend(v for v in kwargs.values() if isinstance(v, Term))
                self.children = tuple(children)

            def execute(self, context: Context) -> ResultT:
                resolved_args = [a.execute(context) if isinstance(a, Term) else a
                                 for a in self._args]
                resolved_kwargs = {k: v.execute(context) if isinstance(v, Term) else v
                                   for k, v in self._kwargs.items()}
                return self._func(*resolved_args, **resolved_kwargs)
    """

    def _resolve_args(self, context: Context, args: tuple[Any, ...]) -> list[Any]:
        """Resolve positional arguments, executing any Terms.

        Args:
            context: Execution context
            args: Tuple of arguments (may contain Terms)

        Returns:
            List of resolved argument values
        """
        resolved = []
        for arg in args:
            if isinstance(arg, Term):
                resolved.append(arg.execute(context))
            else:
                resolved.append(arg)
        return resolved

    def _resolve_kwargs(self, context: Context, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Resolve keyword arguments, executing any Terms.

        Args:
            context: Execution context
            kwargs: Dict of keyword arguments (may contain Terms)

        Returns:
            Dict of resolved keyword argument values
        """
        resolved = {}
        for key, val in kwargs.items():
            if isinstance(val, Term):
                resolved[key] = val.execute(context)
            else:
                resolved[key] = val
        return resolved

    @abstractmethod
    def execute(self, context: Context) -> ResultT:
        """Execute the N-ary operation.

        Subclasses implement their specific argument handling and execution logic.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        ...
