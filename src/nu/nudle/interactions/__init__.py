"""nudle interactions.

One module per wire interaction. Each interaction's class name lowercased
becomes its op on the wire (see protocol.Frame). To add an interaction,
drop a new module here; refs decide which ones they expose by returning
the corresponding class from their methods.
"""

from __future__ import annotations

from .append import Append
from .changed import Changed
from .write import Write


__all__ = ["Append", "Changed", "Write"]
