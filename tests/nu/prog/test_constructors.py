"""Braces: InProcess and Venv.

The fast tier points a Venv brace at ``sys.executable``. That is not a
foreign venv, but it is a genuinely separate process, so it still exercises
the whole transport: spawn, handshake, frames, cloudpickle round trip,
by-reference vs by-value, diagnostics crossing the wire, child reuse.

The slow tier builds a real throwaway venv and installs a package this
interpreter does not have. That is the only tier that proves the point of a
Venv brace, and it costs a network install, so it is marked ``slow``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest

import nu
from nu.prog.constructors import BraceError, Constructor, InProcess, Venv
from nu.prog.diagnostics import Diagnostic


REPO_ROOT = Path(__file__).resolve().parents[3]


def src(text: str) -> str:
    return textwrap.dedent(text).lstrip()


HELLO = src("""
    import nu

    def out():
        return nu.Str('hi')
""")


@pytest.fixture
def brace():
    with Venv(sys.executable) as b:
        yield b


# -- InProcess ---------------------------------------------------------------


def test_in_process_constructs_and_runs():
    term = InProcess().construct(HELLO)
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "hi"


def test_in_process_returns_a_diagnostic():
    diag = InProcess().construct("def out(:\n    pass\n")
    assert isinstance(diag, Diagnostic)


def test_in_process_is_a_context_manager():
    with InProcess() as b:
        assert isinstance(b.construct(HELLO), nu.Nu)


def test_both_braces_satisfy_the_protocol(brace):
    assert isinstance(InProcess(), Constructor)
    assert isinstance(brace, Constructor)


# -- Venv: the round trip ----------------------------------------------------


def test_venv_constructs_a_term_that_runs_in_the_parent(brace):
    term = brace.construct(HELLO)
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "hi"


def test_shared_vocabulary_arrives_by_reference(brace):
    # nu.Str is importable in the child, so it travels as a name and binds
    # to *this* process's class.
    term = brace.construct(HELLO)
    assert type(term) is nu.Str


def test_snippet_minted_class_arrives_by_value(brace):
    # A Literal is the plainest way to hand a live object back out of a
    # snippet: the class rides in the term's payload, so running the term
    # yields the very object the child made.
    source = src("""
        import nu

        class Movie(nu.Service):
            pass

        def out():
            return nu.Literal(Movie)
    """)
    remote, _ = nu.run(brace.construct(source))
    local, _ = nu.run(InProcess().construct(source))

    # A class the snippet minted is not importable anywhere, so cloudpickle
    # ships the class itself. Its base still resolves by reference.
    assert isinstance(remote, type)
    assert remote.__mro__[1] is nu.Service
    assert remote.__module__ == "__nu_program__"
    # And it is a different object from the identically-named class the
    # in-process brace made. That asymmetry is the design.
    assert remote is not local


def test_tree_built_from_snippet_minted_classes_runs_here(brace):
    source = src("""
        import nu

        class Calculator:
            def add(self, a, b):
                return a + b

        class Calc(nu.Service):
            add = nu.service.QueryRef.method()

        def out():
            return nu.With(
                nu.service.bind(Calc, target=Calculator()),
                body=Calc.add(a=2, b=3),
            )
    """)
    term = brace.construct(source)
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == 5


def test_scope_binds_by_parameter_name(brace):
    term = brace.construct(
        src("""
            import nu

            def out(path):
                return nu.Str(path)
        """),
        scope={"path": "sections.s_1", "unused": 1},
    )
    value, _ = nu.run(term)
    assert value == "sections.s_1"


def test_custom_entry_point_name(brace):
    term = brace.construct(
        src("""
            import nu

            def build():
                return nu.Str('x')
        """),
        entry="build",
    )
    assert isinstance(term, nu.Nu)


# -- Venv: diagnostics cross the wire ---------------------------------------


def test_syntax_error_comes_back_as_a_diagnostic(brace):
    diag = brace.construct("import nu\n\ndef out(:\n    return 1\n")
    assert isinstance(diag, Diagnostic)
    assert "does not parse" in diag.message
    assert diag.lineno == 3


def test_snippet_raise_comes_back_with_its_traceback(brace):
    diag = brace.construct(
        src("""
            import nu

            def out():
                return 1 / 0
        """)
    )
    assert isinstance(diag, Diagnostic)
    assert diag.lineno == 4
    assert "ZeroDivisionError" in diag.message
    assert "1 / 0" in diag.traceback


def test_filename_is_honoured_across_the_wire(brace):
    diag = brace.construct("def out():\n    return 1 / 0\n", filename="<movies>")
    assert isinstance(diag, Diagnostic)
    assert "<movies>" in diag.traceback


# -- Venv: the child's stdout is the wire ------------------------------------


def test_snippet_output_does_not_corrupt_the_wire(brace):
    noisy = src("""
        import nu
        import os
        import sys

        print('module level chatter')
        sys.stdout.write('more chatter\\n')
        os.write(1, b'raw fd 1 chatter\\n')

        def out():
            print('entry point chatter')
            return nu.Str('quiet')
    """)
    value, _ = nu.run(brace.construct(noisy))
    assert value == "quiet"
    # The frame after the noisy one is the real proof the stream never
    # desynced.
    assert nu.run(brace.construct(HELLO))[0] == "hi"


# -- Venv: lifecycle ---------------------------------------------------------


def test_one_child_serves_many_constructs(brace):
    pid = brace._proc.pid
    for _ in range(3):
        assert nu.run(brace.construct(HELLO))[0] == "hi"
    assert brace._proc.pid == pid


def test_construct_starts_the_child_lazily():
    b = Venv(sys.executable)
    assert not b.started
    try:
        b.construct(HELLO)
        assert b.started
    finally:
        b.close()


def test_close_is_idempotent_and_reaps_the_child():
    b = Venv(sys.executable)
    b.start()
    proc = b._proc
    b.close()
    b.close()
    assert not b.started
    assert proc.poll() is not None


def test_a_closed_brace_starts_a_fresh_child():
    b = Venv(sys.executable)
    with b:
        first = b._proc.pid
    with b:
        assert b._proc.pid != first


# -- Venv: our failures raise, they are not diagnostics ----------------------


def test_missing_interpreter_raises():
    with pytest.raises(BraceError, match="no such python interpreter"):
        Venv("/nonexistent/bin/python")


def test_directory_without_bin_python_raises(tmp_path):
    with pytest.raises(BraceError, match="no bin/python"):
        Venv(tmp_path)


def test_venv_root_resolves_to_its_interpreter():
    root = Path(sys.executable).parent.parent
    if not (root / "bin" / "python").exists():
        pytest.skip("this interpreter does not live in a bin/python layout")
    assert Venv(root).python.name == "python"


def test_an_interpreter_without_nu_raises_rather_than_hanging(tmp_path):
    # A python that starts but cannot import nu never sends the ready frame.
    fake = tmp_path / "python"
    fake.write_text(f"#!{sys.executable} -E -S\nraise SystemExit(3)\n")
    fake.chmod(0o755)
    with pytest.raises(BraceError, match="did not start"):
        Venv(fake).start()


def test_a_child_that_dies_mid_request_raises(brace):
    suicide = src("""
        import os

        os._exit(9)

        def out():
            return None
    """)
    with pytest.raises(BraceError, match="died while constructing"):
        brace.construct(suicide)
    assert not brace.started


def test_an_unpicklable_scope_value_is_our_failure_not_a_diagnostic(brace):
    # A brace takes plain data. Handing it a live lock is the caller's
    # mistake, not the snippet's, so it raises where the caller stands.
    with pytest.raises(TypeError):
        brace.construct(HELLO, scope={"lock": threading.Lock()})
    # The child never saw the request, so the brace is still usable.
    assert nu.run(brace.construct(HELLO))[0] == "hi"


# -- slow tier: a genuinely foreign venv ------------------------------------


# The dependency the foreign venv gets and this interpreter does not. Small,
# pure python, and stable enough to install in a test.
FOREIGN_DEP = "six"


def build_foreign_venv(root):
    """Make a venv with this repo and FOREIGN_DEP in it."""
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is needed to build the throwaway venv")
    install = [
        uv,
        "pip",
        "install",
        "--python",
        str(root / "bin" / "python"),
        # The kernel package, not the repo root: the root is a virtual uv
        # workspace and has nothing to install. These snippets only touch
        # kernel atoms (nu.Str / nu.Literal), so nustd is not needed.
        str(REPO_ROOT / "packages" / "nucore"),
        FOREIGN_DEP,
    ]
    subprocess.run([uv, "venv", "--python", "3.12", str(root)], check=True)  # noqa: S603
    subprocess.run(install, check=True, env={**os.environ, "VIRTUAL_ENV": str(root)})  # noqa: S603
    return root


@pytest.mark.slow
def test_a_foreign_venv_constructs_against_deps_we_do_not_have(tmp_path):
    # The point of a Venv brace: a program authored against a dependency
    # this interpreter has never heard of still comes home as a live tree.
    with pytest.raises(ImportError):
        __import__(FOREIGN_DEP)
    root = build_foreign_venv(tmp_path / "foreign")

    source = src("""
        import nu
        import six

        def out():
            return nu.Str(six.__name__ + ':' + six.text_type('ok'))
    """)
    with Venv(root) as brace:
        term = brace.construct(source)
    assert isinstance(term, nu.Nu)
    value, _ = nu.run(term)
    assert value == "six:ok"


@pytest.mark.slow
def test_a_foreign_venv_ships_a_class_built_on_a_foreign_dep(tmp_path):
    root = build_foreign_venv(tmp_path / "foreign")

    source = src("""
        import nu
        import six

        class Movie(six.with_metaclass(type, object)):
            title = 'dune'

        def out():
            return nu.Literal(Movie.title)
    """)
    with Venv(root) as brace:
        term = brace.construct(source)
    assert isinstance(term, nu.Literal)
    value, _ = nu.run(term)
    assert value == "dune"
