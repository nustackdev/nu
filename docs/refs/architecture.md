# Ref Architecture

## Full Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 0: PURE PROTOCOL (every/term/ref.py)                         │
│                                                                     │
│  Ref[T]                                                             │
│  ├── resolve(ctx) → Location     # abstract - identity/path         │
│  ├── fetch(ctx) → T | Sentinel   # abstract - value extraction      │
│  ├── execute(ctx) → fetch(ctx)   # concrete - Term compatibility    │
│  └── is_pure = True              # concrete - reading never mutates │
│                                                                     │
│  No parent. No shape. No substrate assumptions. Pure essence.       │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐    ┌─────────────────────────────────────┐
│  PyRef[T]                 │    │  PVRefBase[T]                       │
│  (Python memory)          │    │  (PV substrate root)                │
│  ─────────────────        │    │  ─────────────────                  │
│  _source: T | Term        │    │  _address: PathAddress              │
│                           │    │  _parent: PVRefBase | None          │
│  resolve(): (cls, type)   │    │  _shape: type[Shape] | None         │
│  fetch(): eval _source    │    │                                     │
│                           │    │  resolve(): build Path from chain   │
│  Context: empty           │    │  fetch(): abstract                  │
└───────────────────────────┘    │                                     │
                                 │  Context: root_view + transaction   │
                                 └─────────────────────────────────────┘
                                                 │
                               ┌─────────────────┴─────────────────┐
                               ▼                                   ▼
                ┌─────────────────────────┐     ┌─────────────────────────┐
                │  PVPrimitiveRef[T]      │     │  PVViewRef[T, ViewT]    │
                │  (leaf values)          │     │  (containers)           │
                │  ───────────────────    │     │  ───────────────────    │
                │  _value_type: type[T]   │     │  _view_type: type[V]    │
                │                         │     │                         │
                │  fetch():               │     │  fetch():               │
                │    navigate to parent   │     │    navigate to view     │
                │    return view[key]     │     │    return view          │
                └─────────────────────────┘     └─────────────────────────┘
```

## Type Traits Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1: TYPE TRAITS (everybase/traits/)                           │
│                                                                     │
│  Numeric[T, WrapT]     # __add__, __sub__, __mul__, __neg__, ...    │
│  Comparable[T]         # __lt__, __gt__, __le__, __ge__, __eq__     │
│  Logical[T, WrapT]     # and_(), or_(), not_()                      │
│  Bitwise[T, WrapT]     # __lshift__, __rshift__, __and__, __xor__   │
│  Textual[T, WrapT]     # concat, upper(), lower(), split(), ...     │
│  Indexable[T, WrapT]   # __getitem__, __len__                       │
│                                                                     │
│  All traits use abstract _wrap(op) → WrapT for result wrapping      │
└─────────────────────────────────────────────────────────────────────┘
```

## Type Bases Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 2: TYPE BASES (everybase/refs/)                              │
│                                                                     │
│  RefBase[T]                                                         │
│  ├── Ergonomics: is_empty(), is_invalid(), or_default()            │
│  ├── Conversions: to_int(), to_str(), to_float(), to_bool()        │
│  └── Abstract: fetch(ctx), _wrap(op)                                │
│                                                                     │
│  IntRefBase = Numeric + Comparable + Logical + Bitwise + RefBase    │
│  FloatRefBase = Numeric + Comparable + RefBase                      │
│  StrRefBase = Comparable + Textual + RefBase                        │
│  BoolRefBase = Comparable + Logical + RefBase                       │
│  BytesRefBase = Comparable + Indexable + RefBase                    │
│  ListRefBase = Indexable + RefBase                                  │
│  DictRefBase = Indexable + RefBase                                  │
│  SetRefBase = RefBase                                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Concrete Refs

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 4: CONCRETE REFS                                             │
│                                                                     │
│  Python Memory:                                                     │
│  ├── IntRef = PyRef[int] + IntRefBase                               │
│  ├── FloatRef = PyRef[float] + FloatRefBase                         │
│  ├── StrRef = PyRef[str] + StrRefBase                               │
│  ├── BoolRef = PyRef[bool] + BoolRefBase                            │
│  └── ...                                                            │
│                                                                     │
│  PV Storage:                                                        │
│  ├── PVIntRef = PVPrimitiveRef[int] + IntRefBase                    │
│  ├── PVStrRef = PVPrimitiveRef[str] + StrRefBase                    │
│  ├── PVDictRef = PVViewRef[T, DictView] + DictRefBase               │
│  └── ...                                                            │
│                                                                     │
│  Each concrete ref implements _wrap(op) to return its own type      │
└─────────────────────────────────────────────────────────────────────┘
```

## Composition Pattern

The pattern for creating a concrete ref:

```python
# 1. Substrate base provides storage
class PyRef[T](Ref[T]):
    def __init__(self, source: T | Term[T]): ...
    def fetch(self, ctx: Context) -> T | Sentinel: ...

# 2. Type base provides operators (uses abstract _wrap)
class IntRefBase(Numeric, Comparable, Logical, Bitwise, RefBase[int], ABC):
    @abstractmethod
    def _wrap(self, op: Term) -> Self: ...

    def __add__(self, other): return self._wrap(AddOp(self, other))

# 3. Concrete ref combines both and implements _wrap
class IntRef(PyRef[int], IntRefBase):
    def _wrap(self, op: Term) -> IntRef:
        return IntRef(op)
```

## Verb Usage by Layer

| Component | resolve() | fetch() | execute() | get() |
|-----------|-----------|---------|-----------|-------|
| every.Ref | abstract | abstract | calls fetch | - |
| PyRef | trivial | eval source | inherited | - |
| PVRefBase | build path | abstract | inherited | - |
| PVPrimitiveRef | inherited | view[key] | inherited | - |
| PVViewRef | inherited | return view | inherited | - |
| Shapes/Views | - | - | - | user-facing |
