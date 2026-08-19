"""Law: a declarative validity rule, plus the verdict primitives and runners.

A ``Law`` judges one node: ``scope`` selects nodes it applies to, ``holds``
must be true on each. When ``holds`` is false the law yields a ``Violation``
at the given ``Severity``. The subtree-wide check belongs in a synthesized
attribute; the law itself stays a flat predicate over one node.

- ``Severity``        - how hard a failure bites (``ERROR`` or ``WARNING``).
- ``Violation``       - one failure: path, law, detail, severity.
- ``Law``             - the rule.
- ``gate``            - run every law over every node; return every Violation.
- ``validate``        - same, but raise on any error-level Violation.
- ``ValidationError`` - raised by ``validate`` when error-level laws fail.
"""

from __future__ import annotations

import sys as _sys


if _sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as _Enum

    class StrEnum(str, _Enum):
        """Backport of enum.StrEnum for Python 3.10."""

        def __new__(cls, value: str) -> StrEnum:
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def __str__(self) -> str:
            return str.__str__(self)


from typing import TYPE_CHECKING, NamedTuple, TypeAlias


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.engine.compilation import Path, Program

    from .predicate import Test

__all__ = [
    "Law",
    "Message",
    "Severity",
    "ValidationError",
    "Violation",
    "gate",
    "validate",
]

Message: TypeAlias = "str | Callable[[Program, Path], str]"


class Severity(StrEnum):
    """How hard a law's failure bites: a rejection, or a flagged warning."""

    ERROR = "error"
    WARNING = "warning"


class Violation(NamedTuple):
    """One law failure: where it is, which law, why, and how hard it bites."""

    path: Path
    law: str
    detail: str
    severity: Severity


class Law:
    """A declarative validity rule over one node of a compiled Program."""

    def __init__(
        self,
        name: str,
        *,
        scope: Test,
        holds: Test,
        message: Message,
        severity: Severity = Severity.ERROR,
    ) -> None:
        self.name = name
        self.scope = scope
        self.holds = holds
        self.message = message
        self.severity = severity

    def check(self, program: Program, path: Path) -> Violation | None:
        """The Violation this law yields at ``path``, or ``None`` if it holds.

        Returns ``None`` in two distinct cases: the node is out of scope, or
        the predicate holds. Otherwise returns the failure.
        """
        if not self.scope(program, path):
            return None
        if self.holds(program, path):
            return None
        detail = self.message if isinstance(self.message, str) else self.message(program, path)
        return Violation(path, self.name, detail, self.severity)

    def __repr__(self) -> str:
        return f"Law({self.name!r})"


def gate(program: Program, *laws: Law) -> list[Violation]:
    """Run every law over every node and return every Violation found."""
    return [
        violation
        for path in program.walk()
        for law in laws
        if (violation := law.check(program, path)) is not None
    ]


def validate(program: Program, *laws: Law) -> Program:
    """Run a gate; raise on any error-level Violation, else return the program.

    Warning-level violations pass through; read them with ``gate`` directly.

    Raises:
        ValidationError: if any law yields an error-level Violation. The
            error's ``violations`` attribute holds every error-level
            Violation found.
    """
    errors = [v for v in gate(program, *laws) if v.severity is Severity.ERROR]
    if errors:
        raise ValidationError(errors, program=program)
    return program


def _term_names(program: Program, path: Path) -> tuple[str, ...]:
    """Class names of every Term along ``path``, root-first, including target."""
    names: list[str] = []
    cur: Path = ()
    for step in (*path, None):  # sentinel to include the terminal path
        nid = program.id_of.get(cur)
        if nid is None:
            break
        names.append(type(program.terms[nid]).__name__)
        if step is None:
            break
        cur = (*cur, step)
    return tuple(names)


def _render_violation(program: Program | None, v: Violation) -> str:
    """One violation, two lines: ``[law] detail`` then ``at Term path=... chain=Root > ... > Term``."""
    head = f"  [{v.law}] {v.detail}"
    if program is None:
        return f"{head}  at {v.path}"
    try:
        chain = _term_names(program, v.path)
    except (KeyError, IndexError):
        return f"{head}  at {v.path}"
    if not chain:
        return f"{head}  at {v.path}"
    term = chain[-1]
    ancestry = " > ".join(chain)
    return f"{head}\n      at {term}  path={v.path}  chain={ancestry}"


class ValidationError(ValueError):
    """Raised by :func:`validate` when one or more error-level laws fail.

    Subclasses :class:`ValueError` so existing ``except ValueError`` sites
    keep working. The ``violations`` attribute is the full list of
    error-level Violations as found by ``gate``.

    Each violation renders on two lines: ``[law] detail`` then a second line
    with the Term class of the failing node plus the root-to-node ancestry
    chain (e.g. ``at IfDo  (Provide > Flow > ForeverDo > IfDo)``). Falls
    back to the raw path tuple when the program is unavailable.
    """

    def __init__(self, violations: list[Violation], *, program: Program | None = None) -> None:
        self.violations = violations
        self.program = program
        lines = "\n".join(_render_violation(program, v) for v in violations)
        super().__init__(f"invalid program:\n{lines}")
