"""Nu interactions - concrete kinds, organized by the five-kind taxonomy.

interactions/
├── query/
│   ├── scalar/   — single-value Queries (incl. stream-driven Reductions)
│   └── stream/   — multi-value Queries (Filter, Map, Fold, ...)
├── command/      — Scalar Commands (Print, Log, Debug, SkipIf*)
├── flow/         — Strategy + Control concrete kinds
└── span/
└── policy/   — Policy concrete kinds (Retry, TryCatch, Timeout, ...)
"""

from .command import *  # noqa: F403
from .command import __all__ as _command_all
from .flow import *  # noqa: F403
from .flow import __all__ as _flow_all
from .query import *  # noqa: F403
from .query import __all__ as _query_all
from .span import *  # noqa: F403
from .span import __all__ as _span_all


__all__ = [*_query_all, *_command_all, *_flow_all, *_span_all]  # type: ignore
