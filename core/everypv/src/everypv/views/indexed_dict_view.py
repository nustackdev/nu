"""IndexedDictView — dict view with hierarchical internal layout.

Layout under the view's container::

    site/
    ├── __keys__/    # FlatListView — ordered key index
    │   ├── 0: "alice"
    │   ├── 1: "bob"
    │   └── ...
    └── __data__/    # actual dict children (same as DictView)
        ├── alice: {...}
        └── bob: {...}

No /m tree.  Length = len(__keys__).  Data ops route to ``__data__/``,
key ops route to ``__keys__/``.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, ClassVar, cast

from pv.container import Container, ContainerProtocol, ContainerStructure, NodeType
from pv.types import EMPTY, Empty
from pv.view import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildObservableBase,
    ChildPrimitiveSetBase,
    ObservableBase,
    UnsafePrimitiveOpsBase,
)

from .base import StdView
from .flat_list_view import FlatListView


if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Mapping as PyMapping


__all__ = [
    "IndexedDictSliceView",
    "IndexedDictView",
]

_KEYS = "__keys__"
_DATA = "__data__"


class IndexedDictView(
    ObservableBase,
    ChildObservableBase[str | int],
    ChildNavigationBase[str | int],
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
    StdView,
):
    """Dict view with hierarchical internal layout for O(1) key access.

    Stores data in ``__data__/`` child container (same semantics as DictView)
    and key index in ``__keys__/`` child container (FlatListView).

    Example::

        >>> dct = IndexedDictView(container, registry)
        >>> dct.store({"a": 1, "b": 2, "c": 3})
        >>> list(dct.keys())   # reads from __keys__/
        ['a', 'b', 'c']
        >>> view = dct.islice(1, 3)
        >>> list(view.keys())
        ['b', 'c']
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(13)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = dict

    @classmethod
    def is_address_static(cls, address: object) -> bool:
        return True

    def normalize_address(self, address: str | int) -> str | int:
        return address

    # -- Internal containers -----------------------------------------------

    def _data_container(self) -> Container:
        """Container for actual dict data children."""
        return Container(
            ctx=self.container.ctx,
            site=(*self.container.site, _DATA),
        )

    def _keys_view(self) -> FlatListView:
        """FlatListView over ``__keys__/`` child container."""
        container = Container(
            ctx=self.container.ctx,
            site=(*self.container.site, _KEYS),
        )
        return FlatListView(container, self.registry)

    def _ensure_layout(self) -> None:
        """Ensure both child containers exist."""
        self.ensure_created()
        self.container.create_child_container(
            _DATA,
            structure=ContainerStructure(1),  # DictView structure
            protocol=ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE,
            validate=False,
        )
        self.container.create_child_container(
            _KEYS,
            structure=FlatListView.STRUCTURE,
            protocol=FlatListView.PROTOCOL,
            validate=False,
        )

    # -- Read --------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._keys_view())

    def __getitem__(self, address: str | int) -> object | Empty:
        dc = self._data_container()
        child_site = (*dc.site, address)
        from pv.container import node_ops

        node_info = node_ops.get_node_info(child_site, dc.ctx)
        if not node_info.exists or node_info.node_type == NodeType.NOT_FOUND:
            raise KeyError(address)
        if node_info.node_type == NodeType.PRIMITIVE:
            from pv.types import is_empty

            if is_empty(node_info.primitive_value):
                raise KeyError(address)
            return node_info.primitive_value
        # Container child — extract via registry
        from pv.traits import Convertible

        child_container = Container(ctx=dc.ctx, site=child_site)
        child_info = node_info
        if child_info.structure is None:
            raise ValueError(f"Child container '{address}' has no structure ID")
        view_class = self.registry.get_view_for_structure(child_info.structure)
        child_view = view_class(container=child_container, registry=self.registry)
        if not isinstance(child_view, Convertible):
            raise TypeError(f"Child view {view_class.__name__} does not support extraction")
        return child_view.extract()

    def __contains__(self, obj: str | int) -> bool:
        return self._data_container().exists_child(obj)

    def __iter__(self) -> Generator[str | int, None, None]:
        yield from self.keys()

    def key_at(self, idx: int) -> str | int:
        """Get key at index — single O(1) read from __keys__ FlatListView."""
        return self._keys_view()[idx]

    def keys(self) -> Generator[str | int, None, None]:
        kv = self._keys_view()
        if len(kv) == 0:
            # Check if __data__ has children (migration from DictView)
            dc = self._data_container()
            if dc.exists():
                data_keys = list(dc.iter_child_keys(validate=False))
                if data_keys:
                    self._ensure_layout()
                    kv = self._keys_view()
                    kv.store(data_keys)
        yield from kv

    def values(self) -> Generator[object, None, None]:
        for k in self.keys():
            yield self[k]

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        for k in self.keys():
            yield k, self[k]

    def get(self, address: str | int, default: object | Empty = EMPTY) -> object | Empty:
        try:
            return self[address]
        except (KeyError, Exception):
            return default

    # -- Write -------------------------------------------------------------

    def __setitem__(self, address: str | int, value: object) -> None:
        self._ensure_layout()
        dc = self._data_container()
        is_new = not dc.exists_child(address)
        # Write to __data__
        if self.registry.is_container_type(value):
            from pv.traits import Initializable

            value_type = type(value)
            view_class = self.registry.get_view_for_type(value_type)
            structure_id = view_class.get_structure()
            protocol_hints = view_class.get_protocol()
            child_container = dc.create_child_container(
                address,
                structure=ContainerStructure(structure_id),
                protocol=protocol_hints,
            )
            child_view = view_class(container=child_container, registry=self.registry)
            if not isinstance(child_view, Initializable):
                raise TypeError(f"Child view {view_class.__name__} does not support initialization")
            child_view.store(value)
        else:
            dc.put_child_primitive(address, cast("pv.types.Value", value))
        if is_new:
            self._keys_view().append(address)

    def __delitem__(self, address: str | int) -> None:
        self._ensure_layout()
        dc = self._data_container()
        if not dc.exists_child(address):
            raise KeyError(address)
        dc.delete_child(address)
        # Rebuild key index
        kv = self._keys_view()
        remaining = [k for k in kv if k != address]
        kv.store(remaining)

    def clear(self) -> None:
        self._ensure_layout()
        self._data_container().clear_children(validate=False)
        self._keys_view().clear()

    def pop(self, address: str | int, default: object | Empty = EMPTY) -> object | Empty:
        try:
            value = self[address]
            del self[address]
            return value
        except KeyError:
            from pv.types import is_empty

            if is_empty(default):
                raise
            return default

    def update(self, other: PyMapping[str | int, object] | None = None, **kwargs: object) -> None:
        if other:
            for key, value in other.items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value  # type: ignore[assignment]

    # -- Bulk --------------------------------------------------------------

    def store(self, value: PyMapping[str | int, object], *, replace: bool = True) -> None:
        self._ensure_layout()
        if replace and len(self) > 0:
            self.clear()

        keys: list[str | int] = []
        dc = self._data_container()
        for key, val in value.items():
            if self.registry.is_container_type(val):
                from pv.traits import Initializable

                value_type = type(val)
                view_class = self.registry.get_view_for_type(value_type)
                structure_id = view_class.get_structure()
                protocol_hints = view_class.get_protocol()
                child_container = dc.create_child_container(
                    key,
                    structure=ContainerStructure(structure_id),
                    protocol=protocol_hints,
                )
                child_view = view_class(container=child_container, registry=self.registry)
                if not isinstance(child_view, Initializable):
                    raise TypeError(
                        f"Child view {view_class.__name__} does not support initialization"
                    )
                child_view.store(val)
            else:
                dc.put_child_primitive(key, cast("pv.types.Value", val))
            keys.append(key)

        self._keys_view().store(keys)

    def extract(self) -> dict[str | int, object]:
        return {k: self[k] for k in self.keys()}

    # -- Navigation --------------------------------------------------------

    def open_child(self, address, view):
        """Open child view under __data__/."""
        normalized = self.normalize_address(address)
        dc = self._data_container()
        child_site = (*dc.site, normalized)
        child_container = Container(ctx=dc.ctx, site=child_site)
        return view(child_container, self.registry)

    # -- Slice support -----------------------------------------------------

    def islice(self, start: int = 0, stop: int | None = None) -> IndexedDictSliceView:
        """Return a read-only slice view backed by the key index."""
        return IndexedDictSliceView(self, start, stop)


MutableMapping.register(IndexedDictView)


class IndexedDictSliceView:
    """Read-only slice view into an IndexedDictView.

    Reads sliced keys from the ``__keys__`` FlatListView via
    ``extract_range(start, stop)``.

    Example::

        >>> dct = IndexedDictView(container, registry)
        >>> dct.store({"a": 1, "b": 2, "c": 3, "d": 4})
        >>> view = dct.islice(1, 3)
        >>> list(view.keys())  # ['b', 'c']
    """

    _parent: IndexedDictView
    _start: int
    _stop: int | None

    def __init__(
        self,
        parent: IndexedDictView,
        start: int = 0,
        stop: int | None = None,
    ) -> None:
        self._parent = parent
        self._start = start
        self._stop = stop

    def _get_sliced_keys(self) -> list[str | int]:
        kv = self._parent._keys_view()
        stop = self._stop if self._stop is not None else len(kv)
        return cast("list[str | int]", kv.extract_range(self._start, stop))

    def __len__(self) -> int:
        return len(self._get_sliced_keys())

    def __getitem__(self, key: str | int) -> object:
        if key in self._get_sliced_keys():
            return self._parent[key]
        raise KeyError(key)

    def __contains__(self, key: str | int) -> bool:
        return key in self._get_sliced_keys()

    def keys(self) -> Generator[str | int, None, None]:
        yield from self._get_sliced_keys()

    def values(self) -> Generator[object, None, None]:
        for k in self._get_sliced_keys():
            yield self._parent[k]

    def items(self) -> Generator[tuple[str | int, object], None, None]:
        for k in self._get_sliced_keys():
            yield k, self._parent[k]

    def extract(self) -> dict[str | int, object]:
        return {k: self._parent[k] for k in self._get_sliced_keys()}
