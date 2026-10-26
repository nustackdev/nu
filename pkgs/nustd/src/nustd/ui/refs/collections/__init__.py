"""Collection Refs: layer 1 layout. Flat re-exports of every Ref that holds children.

- base:   CollectionRef, the abstract base (the counterpart of LeafRef), and
          the kinds: DictCollectionRef, ListCollectionRef, ShapeCollectionRef.
- container: ContainerRef, the page frame.
- flow:   ColumnRef, RowRef.
- grid:   GridRef, equal cells row after row.
- line:   LineRef, children that run inline like a paragraph.
- chrome: CardRef, BoxRef (the Box), TabsRef, ModalRef,
          AccordionRef, FormRef, FieldsetRef, FieldRef.
- disclosure: CollapsibleRef, SheetRef.
- list:   ListRef, string items first, then any child node as an item.
- page:   PageSectionRef (a titled part of a page), NavListRef (a sidebar
          list or a top bar).
"""

from .base import CollectionRef, DictCollectionRef, ListCollectionRef, ShapeCollectionRef
from .chrome import AccordionRef, BoxRef, CardRef, FieldRef, FieldsetRef, FormRef, ModalRef, TabsRef
from .container import ContainerRef
from .disclosure import CollapsibleRef, SheetRef
from .flow import ColumnRef, RowRef
from .grid import GridRef
from .line import LineRef
from .list import ListRef
from .page import NavListRef, PageSectionRef


__all__ = [
    "AccordionRef",
    "BoxRef",
    "CardRef",
    "CollapsibleRef",
    "CollectionRef",
    "ColumnRef",
    "ContainerRef",
    "DictCollectionRef",
    "FieldRef",
    "FieldsetRef",
    "FormRef",
    "GridRef",
    "LineRef",
    "ListCollectionRef",
    "ListRef",
    "ModalRef",
    "NavListRef",
    "PageSectionRef",
    "RowRef",
    "ShapeCollectionRef",
    "SheetRef",
    "TabsRef",
]
