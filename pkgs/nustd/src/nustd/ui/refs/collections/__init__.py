"""Collection Refs: layer 1 layout. Flat re-exports of every Ref that holds children.

- base:   CollectionRef, the abstract base (the counterpart of LeafRef), and
          the kinds: DictCollectionRef, ListCollectionRef, ShapeCollectionRef.
- container: ContainerRef, the page frame.
- flow:   ColumnRef, RowRef.
- grid:   GridRef, equal cells row after row.
- input_group: InputGroupRef, a field and the buttons that act on it.
- line:   LineRef, children that run inline like a paragraph.
- chrome: CardRef, TabsRef, ModalRef, AccordionRef, FormRef, FieldsetRef,
          FieldRef.
- disclosure: CollapsibleRef, SheetRef.
- list:   ListRef, string items first, then any child as an item.
- page:   PageSectionRef (a titled part of a page), NavListRef (a sidebar
          list or a top bar).
- table:  TableRef, a content table of places, t[r, c]; TableRowRef, one row.
- layout: the four layers every container speaks, and the per child maps.
- order:  the ordering ops of Row, Column, a flowing Grid and List.
- columns: the column record both tables take.
"""

from .base import CollectionRef, DictCollectionRef, ListCollectionRef, ShapeCollectionRef
from .chrome import AccordionRef, CardRef, FieldRef, FieldsetRef, FormRef, ModalRef, TabsRef
from .container import ContainerRef
from .disclosure import CollapsibleRef, SheetRef
from .flow import ColumnRef, RowRef
from .grid import GridRef
from .input_group import InputGroupRef
from .line import LineRef
from .list import ListRef
from .page import NavListRef, PageSectionRef
from .table import TableRef, TableRowRef


__all__ = [
    "AccordionRef",
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
    "InputGroupRef",
    "LineRef",
    "ListCollectionRef",
    "ListRef",
    "ModalRef",
    "NavListRef",
    "PageSectionRef",
    "RowRef",
    "ShapeCollectionRef",
    "SheetRef",
    "TableRef",
    "TableRowRef",
    "TabsRef",
]
