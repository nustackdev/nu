"""The program pipeline: python source in, a running Nu program out.

``LoadNu`` constructs a Nu term from source; ``Eval`` drives the term it
yields. ``PyBrace`` says where the constructing happens - here, or in another
interpreter entirely.
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
