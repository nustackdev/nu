"""Query interactions — functional construction (no mutation)."""

from .scalar import *  # noqa: F401,F403
from .scalar import __all__ as _scalar_all
from .stream import *  # noqa: F401,F403
from .stream import __all__ as _stream_all


__all__ = [*_scalar_all, *_stream_all]
