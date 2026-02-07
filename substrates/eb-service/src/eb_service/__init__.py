"""eb_service -- Service substrate for everybase.

Provides the Interface base class and ServiceMethodCall morphism
for integrating external services into the term algebra.

Services resolve from Context at execution time. Interface methods
return lazy Value terms that compose with eb_shape terms and flows.

Architecture::

    everybase (core: Term, Flow, Context, Span)
    +-- eb_shape     -- document-model substrate (Ref -> nested data navigation)
    +-- eb_service   -- service substrate (Interface -> method terms)
"""

from __future__ import annotations

from .interface import Interface
from .method import method
from .morphisms import ServiceMethodCall


__all__ = [
    "Interface",
    "ServiceMethodCall",
    "method",
]
