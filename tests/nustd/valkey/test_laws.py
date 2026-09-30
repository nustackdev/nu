"""The law gate over ``nustd.valkey`` trees. No server: compile-time only."""

from __future__ import annotations

import pytest

import nu
import nustd
from nustd.valkey import Ping, Url, ValkeyRef, server, url_for


class Scratch(nu.Shape):
    """Where these trees put what they read."""

    u = nustd.mem.ObjectRef.slot()
    p = nustd.mem.ObjectRef.slot()


TREES = {
    "url": nu.With(server("/nonexistent/vk"), body=Scratch.u.set(Url())),
    "ping": nu.With(server("/nonexistent/vk"), body=Scratch.p.set(Ping())),
    "fluent": nu.With(
        server("/nonexistent/vk"),
        body=nu.Sequential(
            Scratch.u.set(ValkeyRef().url()),
            Scratch.p.set(ValkeyRef().ping()),
        ),
    ),
    "explicit_ref": nu.With(server("/nonexistent/vk"), body=Url(ValkeyRef())),
}


@pytest.mark.parametrize("name", sorted(TREES))
def test_validate_passes(name):
    nu.validate(nu.compile(TREES[name]))


@pytest.mark.parametrize("sort", [Url, Ping])
def test_reads_are_scalar_queries(sort):
    assert isinstance(sort(), nu.ScalarQuery)


def test_the_fluent_form_puts_the_receiver_in_the_server_slot():
    ref = ValkeyRef()
    assert nu.tree.children(ref.url())[0] is ref
    assert nu.tree.children(ref.ping())[0] is ref
    assert type(ref.url()) is Url
    assert type(ref.ping()) is Ping


def test_the_atoms_carry_no_caller_value_in_payload():
    for atom in (Url(), Ping()):
        assert not nu.tree.payload(atom)


def test_building_the_preset_starts_nothing():
    """A preset is a spec; the server exists only while the bracket is open."""
    bracket = server("/nonexistent/vk")
    assert isinstance(bracket, nu.Provide)
    assert url_for("/nonexistent/vk").startswith("unix:///tmp/nu-vk-")


def test_importing_the_fabric_does_not_import_the_binary_package():
    """Workers import it to build a URL; the server package loads only on start."""
    import subprocess
    import sys

    code = "import sys, nustd; nustd.valkey.url_for('/x'); print('valkeylite' in sys.modules)"
    out = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "False"
