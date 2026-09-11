"""What the taxonomy says about a class: kind, sort, cardinality, abstract.

Every Nu term is placed by ``nu.lang.kinds``, whether it is an atom, a Form
or a Ref, so the four answers are the same four questions for all three and
they are derived once here rather than per kind.

None of it is written by hand. ``kind`` is the most specific
``nu.lang.kinds`` base in the MRO; ``sort`` and ``cardinality`` are read off
the class's ``_attributes``, which the kind declaration fills in; ``abstract``
is membership of the taxonomy itself, which is what tells ``Query`` apart
from an atom that happens to have written nothing down.
"""

from __future__ import annotations

from typing import Any

from nu.lang import kinds


__all__ = [
    "KIND_CLASSES",
    "declared",
    "is_abstract",
    "kind_of",
    "taxonomy",
]


# The taxonomy bases themselves, in export order. A class that *is* one of
# these is a rung of the ladder rather than something a person composes.
KIND_CLASSES: tuple[type, ...] = tuple(
    getattr(kinds, name) for name in kinds.__all__ if isinstance(getattr(kinds, name), type)
)


def taxonomy(cls: type) -> dict[str, Any]:
    """The four derived facts, ready to splat into a kind's record."""
    return {
        "kind": kind_of(cls),
        "sort": declared(cls, "sort"),
        "cardinality": declared(cls, "cardinality"),
        "abstract": is_abstract(cls),
    }


def kind_of(cls: type) -> str:
    """The most specific ``nu.lang.kinds`` base of ``cls``, or empty."""
    for base in cls.__mro__:
        if base in KIND_CLASSES:
            return base.__name__
    return ""


def declared(cls: type, name: str) -> str:
    """One ``_attributes`` entry of ``cls`` as text, or empty when unset."""
    attribute = getattr(cls, "_attributes", {}).get(name)
    if attribute is None:
        return ""
    value = getattr(attribute, "value", None)
    return getattr(value, "value", None) or str(value)


def is_abstract(cls: type) -> bool:
    """Whether ``cls`` is a taxonomy base rather than a usable subject.

    ``nu.lang`` exports the ladder alongside everything else, so a catalogue
    over it returns ``Query`` and ``Span`` next to real atoms. They carry no
    args, no yields and no example because there is nothing to write, not
    because someone skipped them, and only this tells the two apart.
    """
    return cls in KIND_CLASSES
