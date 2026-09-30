"""Terms never silently turn into Python values.

``bool()``, ``in`` and ``len()`` must return plain Python values, so on a term
they raise with the explicit spelling. ``==`` / ``!=`` build a comparison on a
Form (and a Ref carrying one) and raise on a bare term. Hashing stays identity
based everywhere. The guard at the bottom walks every public Nu class exported
from ``nu`` and ``nustd`` and fails if any of that slips.
"""

from __future__ import annotations

import dataclasses
import importlib
import pkgutil

import pytest

import nu
import nustd
from nu.lang import EMPTY, Form


def _terms() -> list[object]:
    """One term per family: an interaction, a flow, a Form, a Ref with a Form."""
    return [
        nu.Add(1, 2),
        nu.Sequential(nu.Delay(0), nu.Delay(0)),
        nu.Int(1),
        nu.List.of(1, 2),
        nu.Str("ab"),
        nu.IntRef("n"),
        nu.ObjectRef("x"),
    ]


# --- blocked protocol dunders ----------------------------------------------


@pytest.mark.parametrize("term", _terms(), ids=lambda t: type(t).__name__)
def test_bool_raises_with_a_hint(term: object) -> None:
    with pytest.raises(TypeError, match=r"no truth value.*nu\.If"):
        bool(term)
    with pytest.raises(TypeError, match="no truth value"):
        if term:  # the everyday spelling of the same trap
            pass


@pytest.mark.parametrize("term", _terms(), ids=lambda t: type(t).__name__)
def test_in_raises_with_a_hint(term: object) -> None:
    with pytest.raises(TypeError, match=r"`x in t` can't build a term"):
        1 in term  # noqa: B015


@pytest.mark.parametrize("term", _terms(), ids=lambda t: type(t).__name__)
def test_len_raises_with_a_hint(term: object) -> None:
    with pytest.raises(TypeError, match=r"len\(t\) can't build a term.*nu.tree.size"):
        len(term)  # type: ignore[arg-type]


def test_hints_name_the_method_the_term_has() -> None:
    with pytest.raises(TypeError, match=r"use t\.len\(\)"):
        len(nu.Str("ab"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"use nu\.Len\(t\)"):
        len(nu.Add(1, 2))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"use t\.contains\(x\)"):
        "a" in nu.Str("ab")  # noqa: B015
    with pytest.raises(TypeError, match=r"use nu\.Contains\(t, x\)"):
        1 in nu.Int(1)  # noqa: B015
    with pytest.raises(TypeError, match=r"\.and_\(\), \.or_\(\), \.not_\(\)"):
        bool(nu.Int(1) > 0)
    with pytest.raises(TypeError, match=r"nu\.And, nu\.Or, nu\.Not"):
        bool(nu.Add(1, 2))


# --- iteration -------------------------------------------------------------------


_ITER_HINT = r"can't be looped over.*nu\.ForEachDo.*nu\.tree\.preorder"


@pytest.mark.parametrize("term", _terms(), ids=lambda t: type(t).__name__)
def test_iter_raises_with_a_hint(term: object) -> None:
    with pytest.raises(TypeError, match=_ITER_HINT):
        iter(term)  # type: ignore[call-overload]


def test_iter_hint_names_the_spelling_the_term_has() -> None:
    with pytest.raises(TypeError, match=r"t\.iter\(\) for a stream"):
        iter(nu.List.of(1, 2))  # type: ignore[call-overload]
    with pytest.raises(TypeError, match=r"t\.iter\(\) for a stream"):
        iter(nu.Object([1]))  # type: ignore[call-overload]
    with pytest.raises(TypeError, match=r"nu\.Iter\(t\) for a stream"):
        iter(nu.Add(1, 2))  # type: ignore[call-overload]
    with pytest.raises(TypeError, match=r"nu\.Iter\(t\) for a stream"):
        iter(nu.Int(1))  # type: ignore[call-overload]
    with pytest.raises(TypeError, match=r"it\.first\(\) for its first item"):
        iter(nu.List.of(1).iter())  # type: ignore[call-overload]


def test_python_loops_over_a_term_raise_at_once_instead_of_looping() -> None:
    with pytest.raises(TypeError, match=_ITER_HINT):
        for _ in nu.List.of(1, 2):
            pass
    with pytest.raises(TypeError, match=_ITER_HINT):
        _a, _b = nu.List.of(1, 2)  # type: ignore[misc]
    with pytest.raises(TypeError, match=_ITER_HINT):
        list(nu.Object([1, 2]))  # type: ignore[call-overload]
    with pytest.raises(TypeError, match=_ITER_HINT):
        [*nu.Str("ab")]  # type: ignore[misc]


def test_next_raises_with_a_hint() -> None:
    with pytest.raises(TypeError, match=r"can't be looped over.*it\.first\(\)"):
        next(nu.List.of(1, 2).iter())  # type: ignore[call-overload]


def test_iteration_has_explicit_spellings() -> None:
    it = nu.List.of(1, 2).iter()
    assert isinstance(it, nu.Iterator)
    assert isinstance(it, nu.StreamQuery)
    assert isinstance(nu.tree.children(it)[0], nu.Iter)
    assert isinstance(nu.Object([1]).iter(), nu.Iterator)


# --- the iteration spellings run end to end ---------------------------------------


def test_iter_to_list_runs() -> None:
    assert nu.run(nu.List.of(1, 2).iter().to_list())[0] == [1, 2]
    assert nu.run(nu.List.of(1, 1, 2).iter().to_set())[0] == {1, 2}
    assert nu.run(nu.List.of(1, 2).iter().to_tuple())[0] == (1, 2)
    assert nu.run(nu.Object([3, 4]).iter().to_list())[0] == [3, 4]
    assert nu.run(nu.Dict({"a": 1}).keys().iter().to_list())[0] == ["a"]


def test_iter_first_runs() -> None:
    assert nu.run(nu.List.of(1, 2).iter().first())[0] == 1
    assert nu.run(nu.List.of().iter().first())[0] is EMPTY


def test_for_each_do_takes_an_iterator() -> None:
    ctx = nu.Context()
    ctx.attrs["sum"] = 0
    total = nu.IntRef("sum")
    body = total.set(total + nu.IntRef("item"))
    _, ctx = nu.run(nu.ForEachDo(nu.List.of(1, 2, 3).iter(), body), ctx)
    assert ctx.attrs["sum"] == 6


def test_iter_map_and_filter_stay_streams() -> None:
    xs = nu.List.of(1, 2, 3).iter()
    mapped = xs.map(nu.Add(nu.ObjectRef("item"), 1))
    assert isinstance(mapped, nu.Iterator)
    assert nu.run(mapped.to_list())[0] == [2, 3, 4]
    kept = mapped.filter(nu.Gt(nu.ObjectRef("item"), 2))
    assert nu.run(kept.to_list())[0] == [3, 4]
    assert nu.run(nu.Collect(kept))[0] == [3, 4]


async def test_iteration_runs_async() -> None:
    assert (await nu.arun(nu.List.of(1, 2).iter().to_list()))[0] == [1, 2]
    assert (await nu.arun(nu.List.of(5, 6).iter().first()))[0] == 5


def test_itertools_take_an_iterator() -> None:
    import nustd.itertools as it

    pairs = it.pairwise(nu.List.of(1, 2, 3).iter())
    assert nu.run(nu.Collect(pairs))[0] == [(1, 2), (2, 3)]


# --- equality ----------------------------------------------------------------


@pytest.mark.parametrize(
    "term",
    [
        nu.Add(1, 2),
        nu.Sequential(nu.Delay(0), nu.Delay(0)),
        nu.context.attrs.AttrRef("x"),
        nu.Literal(1),
    ],
    ids=lambda t: type(t).__name__,
)
def test_eq_on_a_bare_term_raises(term: object) -> None:
    with pytest.raises(TypeError, match=r"bare term.*nu\.Object\(t\) == x.*nu\.tree\.equal.*`is`"):
        term == 1  # noqa: B015
    with pytest.raises(TypeError, match=r"nu\.Object\(t\) != x"):
        term != 1  # noqa: B015
    with pytest.raises(TypeError, match="bare term"):
        1 == term  # noqa: B015  reflected: int declines, the term answers


@pytest.mark.parametrize(
    "term",
    [nu.Int(1), nu.Object(1), nu.List.of(1), nu.IntRef("n"), nu.None_()],
    ids=lambda t: type(t).__name__,
)
def test_eq_on_a_form_builds_a_comparison(term: object) -> None:
    eq, ne = term == 1, term != 1
    assert isinstance(eq, nu.Bool)
    assert isinstance(ne, nu.Bool)
    assert isinstance(nu.tree.children(eq)[0], nu.Eq)
    assert isinstance(nu.tree.children(ne)[0], nu.Ne)


def test_terms_hash_by_identity_so_dicts_and_sets_still_work() -> None:
    a, b = nu.Int(1), nu.Int(1)
    assert hash(a) == object.__hash__(a)
    seen = {a: "a", b: "b"}
    assert seen[a] == "a"
    assert seen[b] == "b"
    assert len({a, b, a}) == 2


def test_hash_restore_keeps_a_builtins_value_hash() -> None:
    class Tagged(str, nu.Literal):  # a Nu class that also carries a value hash
        def __eq__(self, other: object) -> bool:
            return str.__eq__(self, other)

    assert Tagged.__hash__ is str.__hash__


# --- the guard: every public Nu class ------------------------------------------


def _public_nu_classes() -> list[type]:
    found: dict[str, type] = {}

    def take(module: object) -> None:
        names = getattr(module, "__all__", None) or [
            n for n in dir(module) if not n.startswith("_")
        ]
        for name in names:
            obj = getattr(module, name, None)
            if isinstance(obj, type) and issubclass(obj, nu.Nu):
                found[f"{obj.__module__}.{obj.__qualname__}"] = obj

    for root in (nu, nustd):
        take(root)
        for info in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
            if "demos" in info.name:
                continue
            try:
                module = importlib.import_module(info.name)
            except ImportError:
                continue
            take(module)
    return sorted(found.values(), key=lambda c: f"{c.__module__}.{c.__qualname__}")


PUBLIC = _public_nu_classes()


def _owner(cls: type, name: str) -> type:
    return next(k for k in cls.__mro__ if name in k.__dict__)


def test_the_guard_sees_forms_refs_and_interactions() -> None:
    names = {c.__name__ for c in PUBLIC}
    assert {"Object", "Int", "Dict", "IntRef", "Add", "Race", "Decimal"} <= names
    assert {"ListRef", "ShapeRef", "ItemRef"} <= names
    assert len(PUBLIC) > 300


@pytest.mark.parametrize("cls", PUBLIC, ids=lambda c: f"{c.__module__}.{c.__qualname__}")
def test_public_class_blocks_and_hashes(cls: type) -> None:
    for name in ("__bool__", "__contains__", "__len__", "__iter__", "__next__"):
        assert getattr(cls, name) is getattr(nu.Nu, name), f"{cls}: {name} is overridden"
    assert cls.__hash__ is object.__hash__, f"{cls}: not hashable by identity"
    assert not any(dataclasses.is_dataclass(k) for k in cls.__mro__), f"{cls}: dataclass eq"


@pytest.mark.parametrize("cls", PUBLIC, ids=lambda c: f"{c.__module__}.{c.__qualname__}")
def test_public_class_eq_builds_on_forms_and_raises_elsewhere(cls: type) -> None:
    for name in ("__eq__", "__ne__"):
        method = getattr(cls, name)
        assert method is not object.__dict__[name], f"{cls}: {name} is Python's default"
        owner = _owner(cls, name)
        if issubclass(cls, Form):
            # A Form (or a Ref carrying one) answers with its own comparison.
            assert owner is Form or issubclass(owner, Form), f"{cls}: {name} from {owner}"
        else:
            assert method is getattr(nu.Nu, name), f"{cls}: bare term {name} from {owner}"


def test_a_form_eq_returns_a_term_never_a_python_bool() -> None:
    import nustd.datetime as ndt
    from nustd.decimal import Decimal

    for term in (nu.Int(1), nu.Dict({}).keys(), Decimal.of("1"), ndt.date.of(2026, 1, 1)):
        result = term == term
        assert isinstance(result, nu.Nu)
        assert not isinstance(result, bool)


def test_eq_hint_points_list_membership_at_identity() -> None:
    a, b = nu.Add(1, 2), nu.Add(1, 2)
    assert a in [a]  # Python checks `is` first, so identity membership works
    with pytest.raises(TypeError, match=r"Python list.*compare with `is`.*set or dict"):
        b in [a]  # noqa: B015
    assert {a: 1}[a] == 1


def test_a_queue_has_no_value_equality() -> None:
    from nustd.mem.refs.jqueue import JQueue, JQueueRef

    q = JQueue(nu.Literal(None))
    with pytest.raises(TypeError, match=r"queue has no value equality.*nu\.Int\(q\.qsize\(\)\)"):
        q == 1  # noqa: B015
    with pytest.raises(TypeError, match="queue has no value equality"):
        q != 1  # noqa: B015
    assert JQueueRef.__eq__ is JQueue.__eq__


def test_object_attribute_docstring_lists_every_reserved_name() -> None:
    import re

    doc = nu.Object.__getattr__.__doc__ or ""
    listed = set(re.findall(r"`([a-z_]+)`", doc.split("Only names Object does not define")[1]))
    own = {n for n in dir(nu.Object) if not n.startswith("_")}
    assert own <= listed, f"undocumented: {sorted(own - listed)}"
    assert nu.run(nu.Object(nu.GetAttr(nu.Object({"a": 1}), "keys")))[0] is not None
