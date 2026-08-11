"""Service DSL: Service, Method, MethodDescriptor, ServiceMeta.

Flat/capability sibling of Shape. A Service class collects Methods at
class-definition time; each Method exposes as a MethodRef when accessed
on the Service class. Mirrors Shape's Slot / Ref split:

    Shape:   Slot   (decl) -> <Type>Ref  (leaf)
    Service: Method (decl) -> MethodRef  (leaf)

No Interactions here. Concrete dialects (nu.http, later others) subclass
MethodRef and expose their own `.method(...)` factory that packages the
subclass + config as a `Method` declaration.

Example (using nu.http)::

    class GH(Service):
        get_repo    = nu.http.GETRef.method("/repos/{owner}/{name}")
        list_issues = nu.http.GETRef.method("/repos/{owner}/{name}/issues")

    GH.get_repo   # -> GETRef  (descriptor unwraps the Method declaration)
    GH.get_repo(owner="nu", name="core")  # -> HttpGet interaction
"""

from __future__ import annotations

from abc import ABCMeta
from typing import ClassVar

from .refs import MethodRef


__all__ = ["Method", "MethodDescriptor", "Service", "ServiceMeta"]


class Method:
    """Declaration factory: a MethodRef class + its payload kwargs."""

    def __init__(
        self,
        ref_cls: type[MethodRef] = MethodRef,
        **kwargs: object,
    ) -> None:
        self.name: str | None = None
        self.ref_cls = ref_cls
        self.kwargs = kwargs
        self._owner_cls: type | None = None

    def create_ref(self, owner_service: type[Service]) -> MethodRef:
        """Instantiate the MethodRef, wiring owner_service."""
        return self.ref_cls(name=self.name, owner_service=owner_service, **self.kwargs)

    def __repr__(self) -> str:
        return f"<Method name={self.name!r} ref_cls={self.ref_cls.__name__}>"


class MethodDescriptor:
    """Returns a fresh MethodRef when a name is accessed on a Service class."""

    def __init__(self, name: str, method: Method) -> None:
        self.name = name
        self.method = method

    def __get__(self, obj: object, objtype: type[Service] | None = None) -> MethodRef:
        if objtype is None:
            raise TypeError("MethodDescriptor requires a Service class")
        return self.method.create_ref(owner_service=objtype)

    def __set__(self, obj: object, value: object) -> None:
        raise AttributeError(f"Cannot set method '{self.name}': methods are read-only")


class ServiceMeta(ABCMeta):
    """Collects Method declarations and replaces them with MethodDescriptors."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        """Build the Service class, collecting Method declarations."""
        methods: dict[str, Method] = {}
        for base in bases:
            if hasattr(base, "_methods"):
                methods.update(base._methods)

        for field_name, value in list(namespace.items()):
            if isinstance(value, Method):
                value.name = field_name
                methods[field_name] = value

        namespace["_methods"] = methods
        cls = super().__new__(mcs, name, bases, namespace)

        for value in namespace.values():
            if isinstance(value, Method) and value._owner_cls is None:
                value._owner_cls = cls

        for field_name, method in methods.items():
            setattr(cls, field_name, MethodDescriptor(field_name, method))
        return cls


class Service(metaclass=ServiceMeta):
    """Declarative capability set. Never instantiated.

    Methods are replaced by MethodDescriptors at class-definition time.
    All access is at class level.
    """

    _methods: ClassVar[dict[str, Method]] = {}
