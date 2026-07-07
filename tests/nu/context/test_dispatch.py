"""Tests for fabric dispatch: MethodFactory and the ``method_*`` descriptors.

A fabric is a typed Context binding named by a ``FabricRef`` subclass (one
Ref per bound fabric). ``MethodFactory`` builds an atom that resolves the
bound fabric from slot 0 and calls a named method on it; the ``method_query``
/ ``method_action`` / ``method_command`` descriptors are the class-body sugar,
one per base so the effect kind is always named. Coverage drives real calls
over a stub fabric and pins the basis: kind, effect (READ vs WRITE),
determinism, Form wrapping, sentinels, and per-fabric isolation.
"""

from __future__ import annotations

import pytest

from nu.context import FabricRef
from nu.factory import MethodFactory, method_action, method_command, method_query
from nu.forms.primitives import IntForm, StrForm
from nu.lang import (
    INVALID,
    Attr,
    Cardinality,
    Command,
    Context,
    Effect,
    ScalarAction,
    ScalarQuery,
    compile,
)
from nu.lang.helpers import arun, run


class Wallet:
    """A stub fabric: a read, a read with args, an action, a command, an async read."""

    def __init__(self) -> None:
        self.log: list[object] = []

    def balance(self) -> int:
        return 100

    def add(self, a: int, b: int = 0) -> int:
        return a + b

    def send(self, to: str) -> str:
        self.log.append(("send", to))
        return f"sig-{to}"

    def ping(self) -> None:
        self.log.append("ping")

    async def aslot(self) -> int:
        return 7


class WalletRef(FabricRef):
    """Typed fabric interface over ``Wallet``."""

    fabric = Wallet

    balance = method_query(IntForm, "balance")
    plus = method_query(IntForm, "add")  # attr name differs from method name
    send = method_action(StrForm, "send")
    ping = method_command("ping")
    slot = method_query(IntForm, "aslot")


def _bound() -> Context:
    return Context().bind(Wallet, Wallet())


def _effects(term: object) -> frozenset:
    program = compile(term)
    return program.attr(program.root, Attr.COMPOSITION_EFFECTS)


# --- MethodFactory: base kind drives the effect --------------------------


def test_query_base_reads_the_fabric():
    atom = MethodFactory(ScalarQuery, "Read", "balance")
    assert _effects(atom(WalletRef())) == frozenset({(WalletRef, Effect.READ)})


def test_action_base_writes_the_fabric():
    atom = MethodFactory(ScalarAction, "Do", "send")
    assert _effects(atom(WalletRef(), "x")) == frozenset({(WalletRef, Effect.WRITE)})


def test_command_base_writes_the_fabric():
    atom = MethodFactory(Command, "Fire", "ping")
    assert _effects(atom(WalletRef())) == frozenset({(WalletRef, Effect.WRITE)})


def test_fabric_call_is_non_deterministic_by_default():
    program = compile(MethodFactory(ScalarQuery, "Read", "balance")(WalletRef()))
    assert program.attr(program.root, Attr.DETERMINISTIC) is False


def test_determinism_is_overridable():
    atom = MethodFactory(ScalarQuery, "Read", "balance", deterministic=True)
    program = compile(atom(WalletRef()))
    assert program.attr(program.root, Attr.DETERMINISTIC) is True


def test_method_factory_atom_runs_standalone():
    value, _ = run(IntForm(MethodFactory(ScalarQuery, "Read", "balance")(WalletRef())), _bound())
    assert value == 100


# --- method_query ---------------------------------------------------------


def test_query_yields_the_method_result():
    value, _ = run(WalletRef.balance(), _bound())
    assert value == 100


def test_query_is_form_wrapped_and_chains():
    value, _ = run(WalletRef.balance() + 1, _bound())
    assert value == 101


def test_query_passes_positional_and_keyword_args():
    value, _ = run(WalletRef.plus(3, b=4), _bound())
    assert value == 7


def test_query_instance_access_matches_class_access():
    ctx = _bound()
    assert run(WalletRef().balance(), ctx)[0] == run(WalletRef.balance(), ctx)[0]


def test_query_uses_explicit_name_over_attr_name():
    # ``plus`` is declared over the "add" method.
    value, _ = run(WalletRef.plus(2, b=3), _bound())
    assert value == 5


def test_query_effect_is_a_read():
    assert _effects(WalletRef.balance()) == frozenset({(WalletRef, Effect.READ)})


# --- method_action --------------------------------------------------------


def test_action_yields_and_records_its_effect():
    ctx = _bound()
    value, ctx = run(WalletRef.send("alice"), ctx)
    assert value == "sig-alice"
    assert ctx.get(Wallet).log == [("send", "alice")]


def test_action_effect_is_a_write():
    assert _effects(WalletRef.send("x")) == frozenset({(WalletRef, Effect.WRITE)})


# --- method_command -------------------------------------------------------


def test_command_returns_a_raw_command_not_a_form():
    assert isinstance(WalletRef.ping(), Command)


def test_command_is_void():
    program = compile(WalletRef.ping())
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.VOID


def test_command_runs_for_effect():
    ctx = _bound()
    _, ctx = run(WalletRef.ping(), ctx)
    assert ctx.get(Wallet).log == ["ping"]


# --- async ----------------------------------------------------------------


async def test_query_awaits_an_async_method():
    value, _ = await arun(WalletRef.slot(), _bound())
    assert value == 7


# --- sentinels ------------------------------------------------------------


def test_unbound_fabric_short_circuits():
    value, _ = run(WalletRef.balance(), Context())
    assert value is INVALID


# --- fabric isolation -----------------------------------------------------


def test_distinct_refs_are_distinct_fabrics():
    class OtherRef(FabricRef):
        fabric = Wallet

        balance = method_query(IntForm, "balance")

    # Same underlying fabric type, but keyed by the concrete Ref subclass.
    assert _effects(WalletRef.balance()) != _effects(OtherRef.balance())


# --- construction ---------------------------------------------------------


def test_fabricref_without_a_bound_fabric_raises():
    with pytest.raises(TypeError, match="no bound fabric"):
        FabricRef()
