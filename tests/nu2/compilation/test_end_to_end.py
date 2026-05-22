"""End-to-end: a POC-style layer-1 slice run on the compilation layer.

Construct -> compile -> read attributes -> gate, with declared, synthesized,
and inherited attributes all in play.
"""

from __future__ import annotations

import pytest

from nu2.engine import Attribute, Law, Schema, Term, compile, gate, validate


_SORT_PARENT = {"ScalarQuery": "Query", "Ref": "Query", "Literal": "Query", "ScalarCmd": "Command"}


def _subsort(a, b):
    while a is not None:
        if a == b:
            return True
        a = _SORT_PARENT.get(a)
    return False


def _child_paths(program, path):
    path_of = program.path_of
    return [path_of[c] for c in program.children[program.id_of[path]]]


def _own_effects(program, path):
    declared = program.attr(path, "own_effects")
    children = _child_paths(program, path)
    out = set()
    for slot, eff in declared.items():
        child = children[slot]
        if _subsort(program.attr(child, "sort"), "Ref"):
            out.add((program.payload(child)["name"], eff))
    for i, child in enumerate(children):
        if i not in declared and _subsort(program.attr(child, "sort"), "Ref"):
            out.add((program.payload(child)["name"], "read"))
    return frozenset(out)


def build_schema():
    schema = Schema()
    schema.register(Attribute.declared({}, name="own_effects"))
    schema.register(
        Attribute.synthesized(
            "tracked_effects",
            base=_own_effects,
            combine=lambda own, children: frozenset(own).union(*children),
            reads=("own_effects", "sort"),
        )
    )
    schema.register(
        Attribute.synthesized(
            "is_pure",
            base=lambda program, path: not program.attr(path, "tracked_effects"),
            combine=lambda own, children: own and all(children),
            reads=("tracked_effects",),
        )
    )
    schema.register(
        Attribute.inherited(
            "ancestor_kinds",
            root=lambda program, path: (),
            derive=lambda program, parent, slot, up: (*up, program.kind(parent).__name__),
        )
    )
    return schema.finalize()


class Ref(Term):
    sort = Attribute.declared("Ref")

    def __init__(self, name):
        super().__init__()
        self.payload = {"name": name}


class Literal(Term):
    sort = Attribute.declared("Literal")

    def __init__(self, value):
        super().__init__()
        self.payload = {"value": value}


class Add(Term):
    sort = Attribute.declared("ScalarQuery")


class Put(Term):
    sort = Attribute.declared("ScalarCmd")
    own_effects = Attribute.declared({0: "write"})


put_target = Law(
    "put_target",
    scope=lambda program, path: program.kind(path) is Put,
    holds=lambda program, path: program.kind(_child_paths(program, path)[0]) is Ref,
    message="Put slot 0 must be a Ref",
)


@pytest.fixture
def schema():
    return build_schema()


def test_dependency_order(schema):
    order = schema.order()
    assert order.index("tracked_effects") < order.index("is_pure")


def test_construct_compile_read(schema):
    counter = Ref("counter")
    program = compile(Put(counter, Add(counter, Literal(1))), schema)

    # synthesized: purity folds bottom-up.
    assert program.attr(program.root, "is_pure") is False
    assert program.attr((1, 0), "is_pure") is True

    # inherited: ancestor kinds thread top-down; shared Ref, two paths.
    assert program.term((0,)) is program.term((1, 0))
    assert program.attr((0,), "ancestor_kinds") == ("Put",)
    assert program.attr((1, 0), "ancestor_kinds") == ("Put", "Add")

    # the root's tracked_effects holds the write.
    effects = program.attrs["tracked_effects"][0]
    assert any(e == "write" for _, e in effects)


def test_gate_and_validate(schema):
    valid = compile(Put(Ref("c"), Literal(1)), schema)
    assert gate(valid, put_target) == []
    assert validate(valid, put_target) is valid

    invalid = compile(Put(Literal(0), Literal(1)), schema)
    verdict = gate(invalid, put_target)
    assert len(verdict) == 1 and verdict[0].law == "put_target"
    with pytest.raises(ValueError, match="put_target"):
        validate(invalid, put_target)
