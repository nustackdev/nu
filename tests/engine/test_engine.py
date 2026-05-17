"""End-to-end: a POC-style layer-1 slice run on the engine.

Construct -> compile -> query -> gate, with declared, synthesized, and
inherited attributes all in play.
"""

from __future__ import annotations

import pytest

from nu.engine import Attribute, Schema, Symbol, Violation, compile, gate, validate


_SORT_PARENT = {"ScalarQuery": "Query", "Ref": "Query", "Literal": "Query", "ScalarCmd": "Command"}


def _subsort(a, b):
    while a is not None:
        if a == b:
            return True
        a = _SORT_PARENT.get(a)
    return False


def _own_effects(program, path):
    declared = program.attr(path, "own_effects")
    kids = program.children(path)
    out = set()
    for slot, eff in declared.items():
        child = kids[slot]
        if _subsort(program.attr(child, "sort"), "Ref"):
            out.add((program.payload(child)["name"], eff))
    for i, child in enumerate(kids):
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
            combine=lambda own, kids: frozenset(own).union(*kids),
            reads=("own_effects", "sort"),
        )
    )
    schema.register(
        Attribute.synthesized(
            "is_pure",
            base=lambda program, path: not program.attr(path, "tracked_effects"),
            combine=lambda own, kids: own and all(kids),
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


class Ref(Symbol):
    sort = Attribute.declared("Ref")

    def __init__(self, name):
        super().__init__()
        self.payload = {"name": name}


class Literal(Symbol):
    sort = Attribute.declared("Literal")

    def __init__(self, value):
        super().__init__()
        self.payload = {"value": value}


class Add(Symbol):
    sort = Attribute.declared("ScalarQuery")


class Put(Symbol):
    sort = Attribute.declared("ScalarCmd")
    own_effects = Attribute.declared({0: "write"})


def rule_put_target(program, path):
    if program.kind(path) is Put and program.kind(program.children(path)[0]) is not Ref:
        yield Violation(path, "SLOT", "Put slot 0 must be a Ref")


@pytest.fixture
def schema():
    return build_schema()


def test_dependency_order(schema):
    order = schema.order()
    assert order.index("tracked_effects") < order.index("is_pure")


def test_construct_compile_query(schema):
    counter = Ref("counter")
    program = compile(Put(counter, Add(counter, Literal(1))), schema)

    # synthesized: purity folds bottom-up.
    assert program.attr(program.root, "is_pure") is False
    assert program.attr((1, 0), "is_pure") is True

    # inherited: ancestor kinds thread top-down; shared Ref, two paths.
    assert program.symbol((0,)) is program.symbol((1, 0))
    assert program.attr((0,), "ancestor_kinds") == ("Put",)
    assert program.attr((1, 0), "ancestor_kinds") == ("Put", "Add")

    # the relation queries.
    writes = program.attr.rows(name="tracked_effects").where(
        lambda r: any(e == "write" for _, e in r["value"])
    )
    assert sorted(writes.paths()) == [()]


def test_gate_and_validate(schema):
    valid = compile(Put(Ref("c"), Literal(1)), schema)
    assert gate(valid, rule_put_target) == []
    assert validate(valid, rule_put_target) is valid

    invalid = compile(Put(Literal(0), Literal(1)), schema)
    verdict = gate(invalid, rule_put_target)
    assert len(verdict) == 1 and verdict[0].rule == "SLOT"
    with pytest.raises(ValueError, match="SLOT"):
        validate(invalid, rule_put_target)
