"""Unit tests for the Service DSL primitives at nu.domains.service.

Covers `Service` / `ServiceMeta` (collects Method declarations, replaces them
with `MethodDescriptor`s), `Method` (declaration factory, names itself at
class-creation time, wires owner_cls), and `MethodRef` (leaf Ref, payload
snapshot). The fabric-side behavior is exercised in test_service_fabric.py;
here we only check the DSL machinery.
"""

from __future__ import annotations

import pytest

from nu.domains.service import (
    Method,
    MethodDescriptor,
    Service,
    ServiceMeta,
)
from nu.domains.service.refs import MethodRef


# --- Service / ServiceMeta ---------------------------------------------------


def test_meta_collects_method_declarations_into_registry():
    class S(Service):
        one = MethodRef.method()
        two = MethodRef.method()

    assert set(S._methods) == {"one", "two"}
    assert all(isinstance(m, Method) for m in S._methods.values())


def test_meta_names_methods_after_their_class_attribute():
    class S(Service):
        endpoint_a = MethodRef.method()

    assert S._methods["endpoint_a"].name == "endpoint_a"


def test_meta_replaces_methods_with_descriptors_on_the_class():
    class S(Service):
        one = MethodRef.method()

    raw = type(S).__mro__[0].__dict__.get("one") or S.__dict__.get("one")
    assert isinstance(raw, MethodDescriptor)


def test_meta_records_owner_cls_on_the_method():
    class S(Service):
        one = MethodRef.method()

    assert S._methods["one"]._owner_cls is S


def test_subclass_inherits_parent_methods():
    class Base(Service):
        one = MethodRef.method()

    class Child(Base):
        two = MethodRef.method()

    assert set(Child._methods) == {"one", "two"}


def test_service_has_service_meta_metaclass():
    assert isinstance(Service, ServiceMeta)


# --- MethodDescriptor -------------------------------------------------------


def test_descriptor_returns_methodref_when_accessed_on_class():
    class S(Service):
        one = MethodRef.method()

    ref = S.one
    assert isinstance(ref, MethodRef)


def test_descriptor_ref_carries_name_and_owner_service():
    class S(Service):
        one = MethodRef.method()

    ref = S.one
    assert ref._payload["name"] == "one"
    assert ref._payload["owner_service"] is S


def test_descriptor_requires_a_class():
    desc = MethodDescriptor("x", Method(MethodRef))
    with pytest.raises(TypeError, match="Service class"):
        desc.__get__(None, None)


# --- MethodRef payload ------------------------------------------------------


def test_methodref_extra_kwargs_land_in_payload():
    class Custom(MethodRef):
        pass

    class S(Service):
        one = Custom.method(path="/x", extra=42)

    ref = S.one
    assert ref._payload["path"] == "/x"
    assert ref._payload["extra"] == 42


def test_method_factory_captures_ref_class_and_kwargs():
    class Custom(MethodRef):
        pass

    decl = Custom.method(a=1, b=2)
    assert isinstance(decl, Method)
    assert decl.ref_cls is Custom
    assert decl.kwargs == {"a": 1, "b": 2}
