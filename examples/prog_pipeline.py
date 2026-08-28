"""The program pipeline: python source in, a running Nu program out.

``LoadNu`` constructs a Nu term from source; ``Eval`` drives the term it
yields. ``PyBrace`` says where the constructing happens - here, or in another
interpreter entirely.

``Program`` is the ergonomic surface over that pair, and ``ProgramRef`` is
the same Form on a storage slot, so a program stored in a fabric runs with
``Shape.job.run()``.
"""

import sys

import nu


# The stored program. It is a module, not an expression, and the reason
# shows: it declares a Shape at module level, which no expression can do.
# The entry point takes `who` from the scope the caller offers.
SOURCE = """
import nu


class Guest(nu.Shape):
    name = nu.mem.StrRef.slot()
    greeting = nu.mem.StrRef.slot()


def out(who):
    return (
        Guest.name.set(who)
        >> Guest.greeting.set(nu.Add("hello ", Guest.name))
        >> nu.print(Guest.greeting)
    )
"""


def demo_bare() -> None:
    print("=" * 60)
    print("1. LoadNu alone: source in, a Nu term out")
    print("=" * 60)

    term, _ = nu.run(nu.LoadNu(SOURCE, scope={"who": "world"}))
    print(f"  loaded: {type(term).__name__}")

    # No brace bound anywhere, so it was built right here.
    print(f"  is a Nu: {isinstance(term, nu.Nu)}")


def demo_in_process_brace() -> None:
    print("=" * 60)
    print("2. Eval(LoadNu(...)) under an in-process brace")
    print("=" * 60)

    tree = nu.Provide(
        nu.prog.PyBrace,
        {},
        nu.Eval(nu.LoadNu(SOURCE, scope={"who": "in-process"})),
    )
    nu.run(tree, nu.Context().bind(dict, {}))


def demo_venv_brace() -> None:
    print("=" * 60)
    print("3. The same program, built in another interpreter")
    print("=" * 60)

    # sys.executable is not a foreign venv, but it is a genuinely separate
    # process: the tree is constructed there and comes home over the wire.
    tree = nu.Provide(
        nu.prog.PyBrace,
        {"python": sys.executable},
        nu.Eval(nu.LoadNu(SOURCE, scope={"who": "venv"})),
    )
    nu.run(tree, nu.Context().bind(dict, {}))


def demo_program_form() -> None:
    print("=" * 60)
    print("5. Program: the same pipeline as a Form")
    print("=" * 60)

    # The verbs are composers, not atoms: what comes back is the tree you
    # would have written by hand.
    tree = nu.Program(SOURCE).run(scope={"who": "form"})
    print(f"  {repr(tree)[:56]}...")
    nu.run(tree, nu.Context().bind(dict, {}))


def demo_program_ref() -> None:
    print("=" * 60)
    print("6. ProgramRef: a program stored in a fabric")
    print("=" * 60)

    class Jobs(nu.Shape):
        greeter = nu.mem.ProgramRef.slot()

    # The source is a stored value like any other string, and the slot
    # carries the verbs, so the store and the run are the same two moves.
    # Two bindings on one dict: the Jobs-scoped one the slot writes through,
    # and an unscoped one the loaded program's own Shape lands in.
    data: dict = {}
    ctx = nu.Context().bind(dict, data).bind(dict, data, Jobs)
    nu.run(Jobs.greeter.set(SOURCE), ctx)
    nu.run(Jobs.greeter.run(scope={"who": "storage"}), ctx)

    # A broken program stored the same way, handled in the tree instead of
    # by a python try block. The catch branch reads the line it died on.
    nu.run(Jobs.greeter.set("import nu\n\ndef out(who):\n    return 1 / 0\n"), ctx)
    line = nu.GetAttr(
        nu.GetAttr(nu.GetAttr(nu.AttrRef("error"), "exception"), "diagnostic"), "lineno"
    )
    caught = nu.run(Jobs.greeter.run(scope={"who": "nobody"}, on_error=line), ctx)[0]
    print(f"  construction failed on line {caught}")


def demo_failure() -> None:
    print("=" * 60)
    print("4. A snippet that does not construct")
    print("=" * 60)

    broken = "import nu\n\ndef out():\n    return 1 / 0\n"
    try:
        nu.run(nu.Eval(nu.LoadNu(broken, filename="<broken>")))
    except nu.prog.ConstructionError as exc:
        print(f"  {exc.diagnostic}")


if __name__ == "__main__":
    demo_bare()
    demo_in_process_brace()
    demo_venv_brace()
    demo_failure()
    demo_program_form()
    demo_program_ref()
