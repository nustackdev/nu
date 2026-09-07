"""Tests for nu.inspect.service - the Service kind."""

from __future__ import annotations

import sys

import nu
import nu.http
from nu.inspect import (
    RefRecord,
    ServiceRecord,
    catalogue_services,
    parse_entry,
    parse_service,
    verify_service,
)
from nu.inspect.entry import entry_names, is_service


class GH(nu.Service):
    """The GitHub endpoints the board syncs against."""

    get_repo = nu.http.GETRef.method("/repos/{owner}/{name}")
    list_issues = nu.http.GETRef.method("/repos/{owner}/{name}/issues", state="open")


def test_a_service_parses_to_prose_plus_one_entry_per_method() -> None:
    record = parse_service(GH, path="app.GH")
    assert isinstance(record, ServiceRecord)
    assert record.summary == "The GitHub endpoints the board syncs against."
    assert [e.name for e in record.entries] == ["get_repo", "list_issues"]


def test_a_method_entry_carries_the_declared_endpoint() -> None:
    entries = {e.name: e for e in parse_service(GH, path="app.GH").entries}
    assert entries["get_repo"].kind == "method"
    assert entries["get_repo"].type == "GETRef"
    assert "path='/repos/{owner}/{name}'" in entries["get_repo"].config
    assert entries["get_repo"].path == "app.GH.get_repo"


def test_the_declared_defaults_ride_on_the_entry_and_nowhere_else() -> None:
    """They are per declaration, so the MethodRef class cannot carry them."""
    entries = {e.name: e for e in parse_service(GH).entries}
    assert "state" in entries["list_issues"].config


def test_a_method_entry_resolves_to_the_method_ref_record() -> None:
    record = parse_entry(GH, "get_repo", path="app.GH.get_repo")
    assert isinstance(record, RefRecord)
    assert record.name == "GETRef"
    assert "a(...)" in {m.spelling for m in record.methods}


def test_an_unknown_method_resolves_to_none() -> None:
    assert parse_entry(GH, "nope") is None


def test_service_marker_and_entry_names() -> None:
    assert is_service(GH)
    assert not is_service(nu.Service)
    assert entry_names(GH) == ("get_repo", "list_issues")


def test_catalogue_finds_the_services_a_module_declares() -> None:
    assert [r.name for r in catalogue_services(sys.modules[__name__])] == ["GH"]


def test_a_service_docstring_that_writes_nothing_extra_is_clean() -> None:
    assert verify_service(GH) == []


def test_args_and_yields_on_a_service_are_violations() -> None:
    class Both(nu.Service):
        """A service that thinks it is the method.

        Args:
            owner: the owner.

        Yields:
            The response.
        """

        get_repo = nu.http.GETRef.method("/repos/{owner}")

    assert {v.rule for v in verify_service(Both)} == {"args-not-callable", "yields-not-a-term"}
