"""Event names -- the vocabulary every notify speaks.

Every notify a node sends names its event in the payload's ``event`` field
(``EVENT``): ``{event: "change", value}``. A Ref's ``on_<event>()`` is the
subscription to exactly that wire name, so the method and the wire never
drift apart.

- ``INPUT``    -- the value is moving: each keystroke, each drag tick
- ``CHANGE``   -- browser-owned state committed: blur, Enter, release, pick,
                  toggle, tab switch, open or close
- ``SUBMIT``   -- the person asked to send
- ``CLICK``, ``ACTION``, ``DISMISS`` -- triggers, no state
- the domain events a ref family sends (a tree's ``RENAME``, a table's
  ``SORT``, an upload's ``PROGRESS``, ...)

``ANY`` is what a catch-all subscription (``on_event()``) watches: every
event the Ref sends.
"""

from __future__ import annotations


__all__ = [
    "ACTION",
    "ADD",
    "ANY",
    "CHANGE",
    "CLICK",
    "COLUMN_ADD",
    "COLUMN_ALIGN",
    "COLUMN_DELETE",
    "COLUMN_KIND",
    "COLUMN_MOVE",
    "COLUMN_RENAME",
    "DELETE",
    "DISMISS",
    "EDIT",
    "EVENT",
    "INPUT",
    "MOVE",
    "OPEN",
    "PROGRESS",
    "RENAME",
    "ROW_CLICK",
    "SELECT",
    "SORT",
    "STATUS",
    "SUBMIT",
    "TOGGLE",
    "UPLOAD",
]


#: The payload field a notify names its event in. A Ref keeps the name for
#: that and sends no field of its own under it.
EVENT = "event"

#: Every event: what a catch-all subscription watches.
ANY = "*"

# --- the shared vocabulary ---------------------------------------------------

#: The value is moving: each keystroke, each drag tick.
INPUT = "input"
#: Browser-owned state committed: blur, Enter, release, pick, toggle, open/close.
CHANGE = "change"
#: The person asked to send what the input (or Form) holds.
SUBMIT = "submit"
#: A trigger was pressed (Button, a chart point).
CLICK = "click"
#: A call to action was taken (EmptyState).
ACTION = "action"
#: The person closed something that only the server can bring back (Alert).
DISMISS = "dismiss"

# --- domain events -----------------------------------------------------------

#: A pick in a tree, a table, a waterfall.
SELECT = "select"
#: A cell edited in place.
EDIT = "edit"
#: A table column sorted.
SORT = "sort"
#: A table row clicked.
ROW_CLICK = "row_click"
#: A tree node or table row dragged to a new place.
MOVE = "move"
#: A tree node opened (activated).
OPEN = "open"
#: A tree node expanded or collapsed.
TOGGLE = "toggle"
#: A tree node renamed in place.
RENAME = "rename"
#: A row added.
ADD = "add"
#: A row deleted.
DELETE = "delete"
#: Table column edits.
COLUMN_ADD = "column_add"
COLUMN_DELETE = "column_delete"
COLUMN_RENAME = "column_rename"
COLUMN_MOVE = "column_move"
COLUMN_KIND = "column_kind"
COLUMN_ALIGN = "column_align"
#: An upload moved forward.
PROGRESS = "progress"
#: An upload finished.
UPLOAD = "upload"
#: A capture's state moved (recording, stopped, ...).
STATUS = "status"
