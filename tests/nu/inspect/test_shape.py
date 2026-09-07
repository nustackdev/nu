"""Tests for nu.inspect.shape and nu.inspect.entry - the Shape kind."""

from __future__ import annotations

import nu
import nu.mem
from nu.inspect import (
    Entry,
    RefRecord,
    ShapeRecord,
    catalogue_shapes,
    parse_entry,
    parse_shape,
    verify_shape,
)
from nu.inspect.entry import entry_names, is_shape, nested_shape
from nu.mem.refs import IntRef, ShapesDictRef, StrRef


class Person(nu.Shape):
    """Whoever a task is assigned to."""

    name: StrRef
    email: StrRef


class Task(nu.Shape):
    """One unit of work on the board.

    Notes:
        - `done` is written only by the reconciler, never by the UI.
    """

    title: StrRef
    priority: IntRef
    owner: Person = nu.mem.ShapeRef.slot(Person)


class Legacy(nu.Shape):
    """A shape written with no annotations at all."""

    title = StrRef.slot()
    owner = nu.mem.ShapeRef.slot(Person)


class Board(nu.Shape):
    """Tasks by id. A collection of shapes is not a nested shape."""

    tasks: ShapesDictRef[int, Task]


# --- the record ------------------------------------------------------------


def test_a_shape_parses_to_prose_plus_one_entry_per_slot() -> None:
    record = parse_shape(Task)
    assert isinstance(record, ShapeRecord)
    assert record.name == "Task"
    assert record.summary == "One unit of work on the board."
    assert record.notes == ("`done` is written only by the reconciler, never by the UI.",)
    assert {e.name for e in record.entries} == {"title", "priority", "owner"}


def test_an_entry_carries_its_kind_type_and_next_path() -> None:
    entries = {e.name: e for e in parse_shape(Task, path="app.Task").entries}
    assert entries["title"] == Entry(
        name="title", kind="ref", type="StrRef", config="", path="app.Task.title"
    )
    assert entries["owner"].kind == "shape"
    assert entries["owner"].type == "Person"
    assert entries["owner"].path == "app.Task.owner"


def test_the_record_is_two_levels_and_never_expands() -> None:
    """A nested shape entry is one line, not the nested shape's own entries."""
    record = parse_shape(Task)
    assert len(record.entries) == 3
    assert all(isinstance(e, Entry) for e in record.entries)


def test_a_parametric_slot_renders_the_declared_type_back() -> None:
    (entry,) = parse_shape(Board).entries
    assert entry.type == "ShapesDictRef[int, Task]"
    assert entry.kind == "ref"


def test_a_slot_with_no_annotation_falls_back_to_the_ref_class() -> None:
    """``_resolve_type_info`` fails soft; the entry still has to say something."""
    entries = {e.name: e for e in parse_shape(Legacy).entries}
    assert entries["title"].type == "StrRef"
    assert entries["owner"].kind == "shape"


# --- one entry down --------------------------------------------------------


def test_a_ref_entry_resolves_to_the_ref_record() -> None:
    record = parse_entry(Task, "title", path="app.Task.title")
    assert isinstance(record, RefRecord)
    assert record.path == "app.Task.title"
    assert ".set(...)" in {m.spelling for m in record.methods}


def test_a_nested_shape_entry_resolves_to_the_shape_record() -> None:
    record = parse_entry(Task, "owner", path="app.Task.owner")
    assert isinstance(record, ShapeRecord)
    assert record.name == "Person"
    assert {e.name for e in record.entries} == {"name", "email"}


def test_a_collection_of_shapes_resolves_to_the_collection_ref() -> None:
    record = parse_entry(Board, "tasks")
    assert isinstance(record, RefRecord)
    assert record.name == "ShapesDictRef"


def test_an_unknown_entry_resolves_to_none() -> None:
    assert parse_entry(Task, "nope") is None


def test_nested_shape_reads_all_three_declaration_forms() -> None:
    assert nested_shape(Task, "owner") is Person
    assert nested_shape(Legacy, "owner") is Person
    assert nested_shape(Task, "title") is None
    assert nested_shape(Board, "tasks") is None


# --- markers and catalogue -------------------------------------------------


def test_shape_marker_excludes_the_base_and_the_refs() -> None:
    assert is_shape(Task)
    assert not is_shape(nu.Shape)
    assert not is_shape(StrRef)
    assert not is_shape("Task")


def test_entry_names_are_empty_for_anything_that_declares_none() -> None:
    assert entry_names(StrRef) == ()
    assert set(entry_names(Task)) == {"title", "priority", "owner"}


def test_catalogue_finds_the_shapes_a_module_declares() -> None:
    import sys

    names = {record.name for record in catalogue_shapes(sys.modules[__name__])}
    assert {"Person", "Task", "Board"} <= names


# --- the contract ----------------------------------------------------------


def test_a_shape_docstring_that_writes_nothing_extra_is_clean() -> None:
    assert verify_shape(Task) == []
    assert verify_shape(Person) == []


def test_args_on_a_shape_is_a_violation_because_a_shape_is_never_called() -> None:
    class Args(nu.Shape):
        """A shape that thinks it is called.

        Args:
            title: the title.
        """

        title: StrRef

    (violation,) = verify_shape(Args)
    assert violation.rule == "args-not-callable"


def test_yields_on_a_shape_is_a_violation_because_a_shape_is_not_a_term() -> None:
    class Yields(nu.Shape):
        """A shape that thinks it evaluates.

        Yields:
            The dict.
        """

        title: StrRef

    (violation,) = verify_shape(Yields)
    assert violation.rule == "yields-not-a-term"


def test_the_shared_laws_still_apply() -> None:
    class Unterminated(nu.Shape):
        """No period here"""

        title: StrRef

    (violation,) = verify_shape(Unterminated)
    assert violation.rule == "summary-unterminated"
