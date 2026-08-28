"""construct: python source -> one Nu term, or a Diagnostic.

Every failure a snippet can cause is a returned Diagnostic, never a
raise, because the same call runs inside a brace that has to ship the
result home.
"""

from __future__ import annotations

import nu
from nu.prog.diagnostics import Diagnostic
from nu.prog.source import construct


# -- happy path --------------------------------------------------------------


def test_returns_the_term() -> None:
    term = construct("import nu\n\ndef out():\n    return nu.Str('hi')\n")
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "hi"


def test_module_level_class_definition() -> None:
    # The reason the unit is a script and not an expression.
    source = (
        "import nu\n"
        "\n"
        "class Movie(nu.Service):\n"
        "    title: str = 'untitled'\n"
        "\n"
        "def out():\n"
        "    return nu.Str(Movie.__name__)\n"
    )
    term = construct(source)
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "Movie"


def test_scope_binds_by_parameter_name() -> None:
    term = construct(
        "import nu\n\ndef out(path):\n    return nu.Str(path)\n",
        scope={"path": "sections.s_1"},
    )
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "sections.s_1"


def test_surplus_scope_keys_are_dropped() -> None:
    # The signature is the contract; offering more than it asks for is fine.
    term = construct(
        "import nu\n\ndef out(path):\n    return nu.Str(path)\n",
        scope={"path": "p", "unused": object()},
    )
    assert isinstance(term, nu.Nu)


def test_parameter_default_stands_in_for_a_missing_offer() -> None:
    term = construct("import nu\n\ndef out(path='fallback'):\n    return nu.Str(path)\n")
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "fallback"


def test_custom_entry_point_name() -> None:
    term = construct("import nu\n\ndef build():\n    return nu.Str('x')\n", entry="build")
    assert isinstance(term, nu.Nu)


# -- diagnostics -------------------------------------------------------------


def test_syntax_error_is_attributed_to_its_line() -> None:
    diag = construct("import nu\n\ndef out(:\n    return 1\n")
    assert isinstance(diag, Diagnostic)
    assert "does not parse" in diag.message
    assert diag.lineno == 3


def test_module_level_raise_is_attributed_to_its_line() -> None:
    diag = construct("import nu\n\nraise ValueError('boom')\n\ndef out():\n    return nu.Str('')\n")
    assert isinstance(diag, Diagnostic)
    assert "boom" in diag.message
    assert diag.lineno == 3


def test_entry_point_raise_is_attributed_to_its_line() -> None:
    diag = construct("import nu\n\ndef out():\n    return 1 / 0\n")
    assert isinstance(diag, Diagnostic)
    assert diag.lineno == 4
    assert "ZeroDivisionError" in diag.message


def test_traceback_carries_the_source_line() -> None:
    # linecache seeding is what makes a snippet frame render its own text.
    diag = construct("import nu\n\ndef out():\n    return 1 / 0\n")
    assert isinstance(diag, Diagnostic)
    assert "1 / 0" in diag.traceback


def test_missing_entry_point() -> None:
    diag = construct("import nu\n\ndef other():\n    return nu.Str('')\n")
    assert isinstance(diag, Diagnostic)
    assert "no entry point 'out'" in diag.message
    assert diag.lineno is None


def test_unbound_parameter_names_what_it_wanted() -> None:
    diag = construct("import nu\n\ndef out(path, space):\n    return nu.Str(path)\n", scope={})
    assert isinstance(diag, Diagnostic)
    assert "path" in diag.message
    assert "space" in diag.message


def test_non_nu_return() -> None:
    diag = construct("def out():\n    return 42\n")
    assert isinstance(diag, Diagnostic)
    assert "returned int" in diag.message


def test_import_error_is_a_diagnostic_not_a_raise() -> None:
    diag = construct("import definitely_not_a_real_module\n\ndef out():\n    return 1\n")
    assert isinstance(diag, Diagnostic)
    assert "definitely_not_a_real_module" in diag.traceback


def test_diagnostic_str_shows_position() -> None:
    diag = Diagnostic(message="broke", lineno=7)
    assert str(diag) == "broke (line 7)"
    assert str(Diagnostic(message="broke")) == "broke"
