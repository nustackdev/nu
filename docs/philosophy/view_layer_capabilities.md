# View Layer — Capabilities

Views are defined by their capabilities, not inheritance.

## Capability Categories

### Conversion

| Protocol        | Method          | Purpose                       |
| --------------- | --------------- | ----------------------------- |
| `Convertible`   | `extract()`     | Container → Python value      |
| `Initializable` | `store(value)`  | Python value → Container      |

These enable bidirectional serialization. A view might support one, both, or neither.

### Access

| Protocol        | Method         | Purpose           |
| --------------- | -------------- | ----------------- |
| `Subscriptable` | `__getitem__`  | Read by address   |
| `Assignable`    | `__setitem__`  | Write by address  |
| `Containable`   | `__contains__` | Membership test   |
| `Sizeable`      | `__len__`      | Item count        |
| `Deletable`     | `__delitem__`  | Remove by address |

### Mutation

| Protocol      | Method              | Purpose                     |
| ------------- | ------------------- | --------------------------- |
| `Appendable`  | `append(value)`     | Add to end                  |
| `Insertable`  | `insert(index, value)` | Add at position             |
| `Poppable`    | `pop(index)`        | Remove and return           |
| `Addable`     | `add(value)`        | Set-like add                |
| `Removable`   | `remove(value)`     | Remove by value (raises)    |
| `Discardable` | `discard(value)`    | Remove by value (silent)    |
| `Clearable`   | `clear()`           | Remove all                  |

### Navigation

| Protocol  | Method                       | Purpose               |
| --------- | ---------------------------- | --------------------- |
| `Nestable` | `open_child(address, view)` | Navigate to child view |

### Observation

| Protocol               | Method                          | Purpose                         |
| --------------------- | ------------------------------- | ------------------------------- |
| `Observable`          | `on_change()`                   | Watch all changes               |
| `ChildObservable`     | `on_child_change(address)`      | Watch specific child            |
| `DescendantsObservable` | `on_descendents_change(*pattern)` | Watch pattern-matched descendants |

## Type Guards

Every protocol has a type guard function:

```python
from everyshape.view import is_subscriptable, is_clearable, is_convertible

def process(view: View) -> dict | None:
    if is_convertible(view):
        return view.extract()  # Type-narrowed to Convertible
    return None
```

## Composition via Mixins

Reusable bases implement common patterns:

```python
class DictView(
    MetadataBasedChildrenCountBase,  # __len__ via metadata
    ChildNavigationBase,             # open_child()
    ChildNestedGetBase,              # _get_child_value()
    ChildNestedSetBase,              # _set_child_value()
    ObservableBase,                  # on_change()
    ViewBase,
):
    ...
```

Each base is single-purpose:

| Base                             | Provides                                       |
| -------------------------------- | ---------------------------------------------- |
| `MetadataBasedChildrenCountBase` | `__len__`, `_increment_length`, `_decrement_length` |
| `LiveChildrenCountBase`          | `__len__` (computed on demand)                  |
| `AddressMappingBase`             | `normalize_address()` hook                      |
| `ChildNavigationBase`            | `open_child()` with address normalization       |
| `ChildNestedGetBase`             | `_get_child_value()` with auto-extraction       |
| `ChildNestedSetBase`             | `_set_child_value()` with auto-population       |
| `ObservableBase`                 | `on_change()` subscription                      |
| `ChildObservableBase`            | `on_child_change()`, `on_children_change()`     |

## View Capability Matrix

Standard views and their capabilities:

| View | Sub | Asgn | Cont | Size | Del | Clr | App | Ins | Pop | Add | Rem | Dis | Conv | Init | Nest |
|------|-----|------|------|------|-----|-----|-----|-----|-----|-----|-----|-----|------|------|------|
| DictView | + | + | + | + | + | + | | | | | | | + | + | + |
| ListView | + | + | + | + | + | + | + | + | + | | | | + | + | + |
| SetView | | | + | + | | + | | | | + | + | + | + | + | |
| QueueView | | | | + | | + | + | | + | | | | + | + | |

Legend: Sub=Subscriptable, Asgn=Assignable, Cont=Containable, Size=Sizeable, Del=Deletable, Clr=Clearable, App=Appendable, Ins=Insertable, Pop=Poppable, Add=Addable, Rem=Removable, Dis=Discardable, Conv=Convertible, Init=Initializable, Nest=Nestable

## Custom Views

Define a view by implementing desired protocols:

```python
class ByteArrayView(
    ObservableBase,
    ChildObservableBase[int],
    MetadataBasedChildrenCountBase,
    StdView,
):
    """ByteArray-like view over container.

    Stores bytes as individual integer children for efficient access.
    Provides bytearray interface with indexing and mutation.

    Example:
        >>> data = ByteArrayView(container, registry)
        >>> data.store(bytearray(b"hello"))
        >>> print(data[0])  # 104 (ord('h'))
        >>> data[0] = 72
        >>> print(data.extract())  # bytearray(b'Hello')
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(6)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED
    CONTAINER_CLS: ClassVar[type] = bytearray

    def normalize_address(self, address: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            address: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if address < 0:
            address = length + address

        if address < 0 or address >= length:
            raise IndexError("bytearray address (index) out of range")

        return address

    def __getitem__(self, address: int) -> int:
        """Get byte at index.

        Args:
            address: Index (supports negative)

        Returns:
            Byte value (0-255)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.normalize_address(address)
        value = self.container.get_child_primitive(normalized)
        if is_empty(value):
            raise IndexError("bytearray index out of range")
        return cast("int", value)
    ...
```

No forced protocols. No mandatory methods. Just what the view needs.

---

Capabilities over inheritance. Composition over hierarchy.
