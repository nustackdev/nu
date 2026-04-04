"""method and prop descriptors, AutoInterface for declarative Type construction.

method: Descriptor that proxies method calls to underlying Python objects.
prop:   Descriptor that proxies property/attribute access.
AutoInterface: Base class that auto-creates method descriptors from annotations.
"""

from __future__ import annotations

import typing
from typing import overload

from nu.interfaces import Interface
from nu.ops.builtins.attr import GetAttrOp
from nu.ops.builtins.call import MethodCallCmd, MethodCallOp
from nu.terms import Ref


__all__ = [
    "AutoInterface",
    "method",
    "prop",
]


class _BoundMethod[V: Interface]:
    """Method descriptor bound to a specific instance.

    Calling this creates a MethodCallOp (pure) or MethodCallCmd (impure)
    op wrapping the call, then wraps it in value_type.
    """

    __slots__ = ("_method_name", "_owner", "_pure", "_value_type")

    def __init__(self, owner: object, value_type: type[V], method_name: str, *, pure: bool) -> None:
        self._owner = owner
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(self._owner, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"{self._owner!r}.{self._method_name}"


class _ClassBoundMethod[V: Interface]:
    """Method descriptor bound to a Ref subclass.

    The Ref subclass itself acts as the factory — calling it creates a
    ref Nu that resolves the target object from context at execution time.

    Example::

        class Solana(Ref):
            get_slot = method(IntI, "getSlot")

        Solana.get_slot()  # → IntI(MethodCallCmd(Solana(), "getSlot"))
    """

    __slots__ = ("_method_name", "_pure", "_ref_cls", "_value_type")

    def __init__(
        self,
        ref_cls: type[Ref],
        value_type: type[V],
        method_name: str,
        *,
        pure: bool,
    ) -> None:
        self._ref_cls = ref_cls
        self._value_type = value_type
        self._method_name = method_name
        self._pure = pure

    def __call__(self, *args: object, **kwargs: object) -> V:
        target = self._ref_cls()
        morph_cls = MethodCallOp if self._pure else MethodCallCmd
        return self._value_type(morph_cls(target, self._method_name, *args, **kwargs))

    def __repr__(self) -> str:
        return f"{self._ref_cls.__name__}.{self._method_name}"


class method[V: Interface]:  # noqa: N801
    """Descriptor that proxies method calls to a Type's underlying object.

    Generic in V (a Interface subclass). Pyright infers the return type.

    Two access modes:

    - **Instance access** (e.g., ``my_str.upper()``): creates MethodCall with
      the instance as target.
    - **Class access on Ref subclass** (e.g., ``Solana.get_slot()``): creates
      MethodCall with a new Ref instance as target (resolved from context
      at execution time).

    Uses ``__set_name__`` to auto-infer the method name from the Python
    attribute name. An explicit name can be provided for APIs with
    different naming conventions.

    Half-code usage::

        class SolanaType(Interface[SolanaClient]):
            get_slot = method(IntI, "getSlot")

    Zero-code usage (via AutoInterface)::

        class StrOps(AutoInterface, Interface[str], pure=True):
            upper: StrI
            lower: StrI
    """

    def __init__(self, value_type: type[V], name: str | None = None, *, pure: bool = False) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._pure = pure
        self._attr_name: str = ""
        self._method_name: str = name or ""

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._method_name = self._explicit_name or attr_name

    @overload
    def __get__(self, obj: None, objtype: type) -> _ClassBoundMethod[V]: ...
    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> _BoundMethod[V]: ...

    def __get__(
        self, obj: object | None, objtype: type | None = None
    ) -> method[V] | _BoundMethod[V] | _ClassBoundMethod[V]:
        if obj is None:
            if objtype is not None and issubclass(objtype, Ref):
                return _ClassBoundMethod(
                    objtype, self._value_type, self._method_name, pure=self._pure
                )
            return self
        return _BoundMethod(obj, self._value_type, self._method_name, pure=self._pure)

    def __repr__(self) -> str:
        name = self._method_name or self._explicit_name or "?"
        purity = "pure" if self._pure else "impure"
        return f"method({self._value_type.__name__}, {name!r}, {purity})"


class prop[V: Interface]:  # noqa: N801
    """Descriptor that proxies property/attribute access on a Type's underlying object.

    Generic in V (a Interface subclass). Pyright infers the return type.

    Two access modes:

    - **Instance access** (e.g., ``my_obj.url``): creates GetAttrOp with
      the instance as target.
    - **Class access on Ref subclass** (e.g., ``MyService.url``): creates
      GetAttrOp with a new Ref instance as target (resolved from context
      at execution time).

    Uses ``__set_name__`` to auto-infer the property name from the Python
    attribute name. An explicit name can be provided for properties with
    different naming conventions (e.g., ``url = prop(StrI, "_url")``).
    """

    def __init__(self, value_type: type[V], name: str | None = None) -> None:
        self._value_type = value_type
        self._explicit_name = name
        self._attr_name: str = ""
        self._prop_name: str = name or ""

    def __set_name__(self, owner: type, attr_name: str) -> None:
        self._attr_name = attr_name
        self._prop_name = self._explicit_name or attr_name

    @overload
    def __get__(self, obj: None, objtype: type) -> V: ...
    @overload
    def __get__(self, obj: object, objtype: type | None = None) -> V: ...

    def __get__(self, obj: object | None, objtype: type | None = None) -> prop[V] | V:
        if obj is None:
            if objtype is not None and issubclass(objtype, Ref):
                return self._value_type(GetAttrOp(objtype(), self._prop_name))
            return self
        return self._value_type(GetAttrOp(obj, self._prop_name))

    def __repr__(self) -> str:
        name = self._prop_name or self._explicit_name or "?"
        return f"prop({self._value_type.__name__}, {name!r})"


class AutoInterface:
    """Base class that auto-creates method descriptors from annotations.

    Inherit alongside Interface. Annotations of Interface subclasses
    become ``method()`` descriptors automatically.

    Usage::

        class StrHelpers(AutoInterface, Interface[str], pure=True):
            upper: StrI
            lower: StrI
            strip: StrI

    Each annotation becomes ``method(AnnotationType, "attr_name", pure=<default>)``.
    Explicit ``method()`` assignments in the class body are preserved.
    """

    def __init_subclass__(cls, *, pure: bool = False, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        own_names = set(cls.__dict__.get("__annotations__", {}))
        if not own_names:
            return

        try:
            hints = typing.get_type_hints(cls)
        except Exception:
            return

        for name in own_names:
            if name.startswith("_"):
                continue
            # Skip if class body already has an explicit value (descriptor, method, etc.)
            if name in cls.__dict__ and name != "__annotations__":
                existing = cls.__dict__[name]
                if not isinstance(existing, type):
                    continue
            hint = hints.get(name)
            if hint is not None and isinstance(hint, type) and issubclass(hint, Interface):
                setattr(cls, name, method(hint, name, pure=pure))
