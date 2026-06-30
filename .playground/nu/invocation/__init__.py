"""Python bridge: a single invocation primitive and a declarative mirror.

    Invoke(fn, *args, **kwargs)
        ScalarQuery that calls a python callable with Nu-resolved args.
        Mode inferred from the callable: `async def` -> ASYNC; plain def -> SYNC.

    Invocation(ReturnType, name=None, *, effects=..., mode=...)
        Descriptor for Ref[T] / TypedNu[T] subclasses. Extracts the target
        python class from the generic parameter, looks up the named method,
        and compiles each call to Invoke(py_method, target, *args).

    FuncCall, FuncCallCmd, MethodCall, MethodCallCmd
        Thin shims that reduce to Invoke. Kept as public API for legacy
        callsites; Cmd variants are structurally identical for now.
"""

from .invoke import FuncCall, FuncCallCmd, Invocation, Invoke, MethodCall, MethodCallCmd


__all__ = [
    "FuncCall",
    "FuncCallCmd",
    "Invocation",
    "Invoke",
    "MethodCall",
    "MethodCallCmd",
]
