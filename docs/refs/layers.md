# Ref Layers

Each layer adds exactly ONE concept. Bottom-up composition.

## Layer 0: Pure Protocol

**Location:** `every/term/ref.py`

**Adds:** The concept of a typed reference

```python
class Ref[T](LValue[T], ABC):
    """Reference to a typed location. Pure essence."""

    @abstractmethod
    def resolve(self, ctx: Context) -> Location:
        """Build identity/location path."""
        ...

    @abstractmethod
    def fetch(self, ctx: Context) -> T | Sentinel:
        """Extract value from this location."""
        ...

    def execute(self, ctx: Context) -> T | Sentinel:
        """Term interface - delegates to fetch."""
        return self.fetch(ctx)

    @property
    def is_pure(self) -> bool:
        """Refs are always pure (reading doesn't mutate)."""
        return True
```

**Key properties:**
- No substrate assumptions
- No parent/child relationships
- No shape associations
- Just: resolve (where) + fetch (what)

## Layer 1: Type Traits

**Location:** `everybase/traits/`

**Adds:** Operator implementations as mixins

```python
class Numeric[T, WrapT]:
    """Numeric operators."""

    @abstractmethod
    def _wrap(self, op: Term) -> WrapT: ...

    def __add__(self, other: T | Ref[T]) -> WrapT:
        return self._wrap(AddOp(self, other))

    def __sub__(self, other: T | Ref[T]) -> WrapT:
        return self._wrap(SubOp(self, other))

    def __neg__(self) -> WrapT:
        return self._wrap(NegOp(self))
    # ...


class Comparable[T]:
    """Comparison operators."""

    def __lt__(self, other: T | Ref[T]) -> BoolRef:
        return BoolRef(LtOp(self, other))

    def __eq__(self, other: T | Ref[T]) -> BoolRef:
        return BoolRef(EqOp(self, other))
    # ...
```

**Key properties:**
- Pure mixins, no storage
- Use abstract `_wrap(op)` for result wrapping
- Comparison always returns BoolRef (cross-substrate)

## Layer 2: Type Bases

**Location:** `everybase/refs/`

**Adds:** Composed traits + ergonomics for each Python type

```python
class RefBase[T](Ref[T], ABC):
    """Ergonomics layer."""

    # Sentinel checks
    def is_empty(self) -> BoolRef: ...
    def is_invalid(self) -> BoolRef: ...
    def or_default(self, default: T) -> AnyRef: ...

    # Type conversions
    def to_int(self) -> IntRef: ...
    def to_str(self) -> StrRef: ...
    def to_float(self) -> FloatRef: ...
    def to_bool(self) -> BoolRef: ...


class IntRefBase(Numeric, Comparable, Logical, Bitwise, RefBase[int], ABC):
    """Integer ref with all applicable traits."""

    @abstractmethod
    def _wrap(self, op: Term) -> Self: ...

    # Arithmetic with type promotion
    def __add__(self, other: int | IntRef) -> Self: ...
    def __add__(self, other: float | FloatRef) -> FloatRef: ...  # promotes
```

**Key properties:**
- Combines traits appropriate for each type
- Handles type promotion (int + float → float)
- Still abstract: `fetch(ctx)` and `_wrap(op)` not implemented

## Layer 3: Substrate Bases

**Location:** Per substrate package

**Adds:** Storage implementation (how to fetch values)

### Python Memory Substrate

```python
# everybase/py/base.py
class PyRef[T](Ref[T]):
    """Python memory substrate."""

    __slots__ = ('_source',)

    def __init__(self, source: T | Term[T]):
        self._source = source

    def resolve(self, ctx: Context) -> Location:
        return (self.__class__.__name__, type(self._source))

    def fetch(self, ctx: Context) -> T | Sentinel:
        if isinstance(self._source, Term):
            return self._source.execute(ctx)
        return self._source
```

### PV Storage Substrate

```python
# every_pv/ref.py
class PVRefBase[T](Ref[T], ABC):
    """PV storage substrate root."""

    __slots__ = ('_address', '_parent', '_shape')

    def __init__(
        self,
        address: PathAddress,
        parent: PVRefBase | None = None,
        shape: type[Shape] | None = None,
    ):
        self._address = address
        self._parent = parent
        self._shape = shape

    def resolve(self, ctx: Context) -> Path:
        """Build path from parent chain."""
        if self._parent is None:
            return ((self._address, self._type),)
        return (*self._parent.resolve(ctx), (self._address, self._type))

    @property
    @abstractmethod
    def _type(self) -> type:
        """The type marker for path segments."""
        ...


class PVPrimitiveRef[T](PVRefBase[T]):
    """PV ref for leaf values."""

    __slots__ = ('_value_type',)

    def __init__(self, value_type: type[T], **kwargs):
        super().__init__(**kwargs)
        self._value_type = value_type

    @property
    def _type(self) -> type:
        return self._value_type

    def fetch(self, ctx: Context) -> T | Sentinel:
        path = self.resolve(ctx)
        root_view = ctx.get_root_view(self._shape)
        parent_view, key = navigate_to_parent(root_view, path)
        return parent_view[key]


class PVViewRef[T, ViewT](PVRefBase[T]):
    """PV ref for container views."""

    __slots__ = ('_view_type',)

    def __init__(self, view_type: type[ViewT], **kwargs):
        super().__init__(**kwargs)
        self._view_type = view_type

    @property
    def _type(self) -> type:
        return self._view_type

    def fetch(self, ctx: Context) -> ViewT:
        path = self.resolve(ctx)
        root_view = ctx.get_root_view(self._shape)
        return navigate_to_view(root_view, path)
```

## Layer 4: Concrete Refs

**Location:** Per substrate package

**Adds:** Final concrete classes combining substrate + type base

```python
# everybase/py/int.py
class IntRef(PyRef[int], IntRefBase):
    """Concrete integer ref for Python memory."""

    def _wrap(self, op: Term) -> IntRef:
        return IntRef(op)


# every_pv/refs/int.py
class PVIntRef(PVPrimitiveRef[int], IntRefBase):
    """Concrete integer ref for PV storage."""

    def __init__(self, address: PathAddress, **kwargs):
        super().__init__(value_type=int, address=address, **kwargs)

    def _wrap(self, op: Term) -> PVIntRef:
        # PV refs wrap morphisms differently - they become Py refs
        # because the result is a computation, not a storage location
        from everybase.py import IntRef
        return IntRef(op)
```

**Note:** When a PV ref is used in an operation (e.g., `pv_int + 5`), the result is a Python memory ref wrapping the morphism, not a new PV ref. The PV ref just provides the value via `fetch()` when the morphism executes.
