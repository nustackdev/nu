"""Shape-specific operations."""

from .collection import (
    CollectionEraseCmd,
    CollectionExistsOp,
    CollectionLoadOp,
    CollectionMissingOp,
    CollectionStoreCmd,
)
from .control import React, ReactForever, ReactWhile, Stream
from .cursor import AdvanceCursorOp
from .item import ItemEraseCmd, ItemExistsOp, ItemLoadOp, ItemMissingOp, ItemStoreCmd
from .reactive import (
    ChangeOp,
    OnChangeOp,
    OnChildChangeOp,
    OnChildrenChangeOp,
    OnDescendantsChangeOp,
    OnPrimitiveChangeOp,
)
