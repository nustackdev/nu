# Defining Your Own Type

How to add a custom domain type to everybase, from abstract operations to substrate-specific Refs.

## Pattern

Every custom type follows this structure:

```
1. Type class   — abstract operations (what you can do with the type)
2. Value class  — computed result (lives in Python memory)
3. RefBase      — get/set methods (how to read/write storage)
4. Substrate Refs — concrete Refs with .slot() for each substrate
```

## Step-by-Step: Solana Pubkey Type

### 1. Define the Type

The Type class inherits from `TypeBase[T]` and optional capability bases. It defines all operations the type supports:

```python
from everybase import Sentinel, StrArg
from everybase.abc import (
    EqualableBase,  # for == and !=
    TypeBase,
    FuncCallOp,
    MethodCallOp,
    BoolValue,
    BytesValue,
    StrValue,
)
from solders.pubkey import Pubkey


class PubkeyType(EqualableBase["Pubkey | PubkeyType"], TypeBase[Pubkey | Sentinel]):
    """What you can do with a Pubkey."""

    # --- Constructors (classmethods return Value) ---

    @classmethod
    def from_string(cls, value: StrArg) -> PubkeyValue:
        return PubkeyValue(FuncCallOp(Pubkey.from_string, value))

    @classmethod
    def from_bytes(cls, b: bytes) -> PubkeyValue:
        return PubkeyValue(FuncCallOp(Pubkey, b))

    # --- Instance methods (return typed Values) ---

    def to_json(self) -> StrValue:
        return StrValue(MethodCallOp(self, "to_json"))

    def to_bytes(self) -> BytesValue:
        return BytesValue(MethodCallOp(self, "__bytes__"))

    def is_on_curve(self) -> BoolValue:
        return BoolValue(MethodCallOp(self, "is_on_curve"))
```

Key points:

- `TypeBase[Pubkey | Sentinel]` — the Python type this wraps, plus Sentinel for absent values
- `EqualableBase` — gives `==` and `!=` operators for free
- Use `ComparableBase` instead if you also want `<`, `>`, `<=`, `>=`
- Constructors are `@classmethod` and return `*Value`
- Methods wrap operations in appropriate Value types

### 2. Define the Value

The Value class is trivial — just dual inheritance:

```python
from everybase.abc import ValueBase

class PubkeyValue(ValueBase, PubkeyType):
    pass
```

That's it. `ValueBase` provides the execution machinery. `PubkeyType` provides all the methods. A Value holds either a literal (`PubkeyValue(some_pubkey)`) or a computation source (`PubkeyValue(FuncCallOp(...))`).

### 3. Define the RefBase

The RefBase defines how to read from and write to storage. Use everyshape tools to build Refs for Shape substrate without much boilerplate.

```python
from everybase import Arg, Term
from everybase.abc import ToStrOp, ensure_term
from everyshape import ItemRef
from everyshape import ItemGetOp, ItemSetCmd


class PubkeyRefBase(ItemRef[Pubkey, PubkeyValue], PubkeyType):
    """How to get/set a Pubkey in any storage."""

    def set(self, value: Arg[Pubkey | str]) -> PubkeyValue:
        # Convert to storage format (base58 string)
        if isinstance(value, Term):
            val = ToStrOp(value)
        else:
            val = str(value)
        return PubkeyValue(ItemSetCmd(self, ensure_term(val)))

    def get(self) -> PubkeyValue:
        # Read from storage (base58 string) and convert back
        return PubkeyValue.from_string(StrValue(ItemGetOp(self)))
```

Key points:

- `ItemRef[Pubkey, PubkeyValue]` — storage type and value type
- Inherits `PubkeyType` so you can call methods directly on the ref: `MyShape.pubkey.is_on_curve()`
- `set()` converts to storage format, `get()` converts back
- Both return `PubkeyValue` — they're lazy terms, not immediate results

#### The `set()` pattern

Every `set()` method follows a two-branch pattern:

```python
def set(self, value: Arg[NativeType | StorageType]) -> MyValue:
    if isinstance(value, Term):
        val = ToStrOp(value)   # or ToIntOp / ToFloatOp
    else:
        val = str(value)       # or int() / float()
    return MyValue(ItemSetCmd(self, ensure_term(val)))
```

How it works:
- **`Arg[T]`** = `T | Term[T] | Term[T | Sentinel]` — accepts both Python objects and term trees
- **Term branch** — wraps in a conversion op (`ToStrOp`, `ToIntOp`, `ToFloatOp`). At runtime, the term resolves to a value and Python's builtin conversion is called on it.
- **Else branch** — direct Python conversion (`str()`, `int()`, `float()`). Works for both native types (via dunders like `__int__`) and raw storage types (identity: `int(42)` → `42`).

For this to work, native classes need the appropriate conversion dunder matching their storage type:
- Stored as `int` → add `__int__` (e.g. `BasisPoint.__int__` returns raw basis points)
- Stored as `float` → add `__float__` (e.g. `Percentage.__float__` returns raw percentage)
- Stored as `str` → `__str__` (usually already present, or use stdlib's `str()`)

**Special cases** (custom storage format that doesn't map to a simple dunder):
- `complex` → stored as `"real,imag"` string, needs `FuncCallOp(format_complex, value)`
- `timezone` → stored as `"+05:30"` offset string, needs `FuncCallOp(format_timezone, value)`
- `Keypair` → stored as base58 of secret key, not `str(keypair)`, needs `FuncCallOp(keypair_to_base58, value)`

### 4. Create Substrate-Specific Refs

For each substrate, create a concrete Ref with `.slot()`:

```python
from typing import Self
from everypv import PrimitiveRef
from eb_dict import RefBase as DictRefBase
from everyshape import Slot


# PV substrate (persistent, reactive)
class PVPubkeyRef(PubkeyRefBase, PrimitiveRef):
    @classmethod
    def slot(cls) -> Self:
        return Slot(cls, value_type=str)  # stored as string in KV store


# Dict substrate (in-memory, simple)
class DictPubkeyRef(PubkeyRefBase, DictRefBase):
    @classmethod
    def slot(cls) -> Self:
        return Slot(cls)  # stored in plain dict
```

### 5. Use in Shapes

```python
from everyshape import Shape

class Token(Shape):
    mint = DictPubkeyRef.slot()
    owner = DictPubkeyRef.slot()
    authority = DictPubkeyRef.slot()
```

### 6. Use in Expressions

```python
from everybase import Context

data = {}
ctx = Context().bind(data, dict, Token)

# Set
await Token.mint.set("So11111111111111111111111111111111111111112").execute(ctx)

# Get
mint = await Token.mint.get().execute(ctx)

# Operations (all lazy until .execute())
is_valid = Token.mint.is_on_curve()
as_json = Token.mint.to_json()
are_equal = Token.mint.get() == Token.owner.get()
```

## Compound Types (dict-stored)

For types with multiple fields (not mappable to a single `int`/`str`/`float`), store as `dict` and use `to_dict()`/`from_dict()` for serialization. Use `@property` on the native class and `GetAttrOp` on the Type for clean property access.

### Native class pattern

```python
class LocalCurve:
    __slots__ = ("_vsol", "_vtok", "_rsol", "_rtok")

    def __init__(self, vsol: int, vtok: int, rsol: int, rtok: int) -> None:
        self._vsol = vsol
        self._vtok = vtok
        self._rsol = rsol
        self._rtok = rtok

    # Serialization — lives on the class, not as free functions
    @classmethod
    def from_dict(cls, d: dict) -> LocalCurve:
        return cls(vsol=d["vsol"], vtok=d["vtok"], rsol=d["rsol"], rtok=d["rtok"])

    def to_dict(self) -> dict:
        return {"vsol": self._vsol, "vtok": self._vtok, "rsol": self._rsol, "rtok": self._rtok}

    # Methods that return new instances (MethodCallOp on Type)
    def apply_buy(self, sol_in: int) -> LocalCurve: ...

    # Properties that return domain types (GetAttrOp on Type)
    @property
    def virtual_sol_reserves(self) -> Lamport:
        return Lamport(self._vsol)

    @property
    def price_lamports(self) -> Lamport:
        return Lamport(self._vsol * 1_000_000 // self._vtok)
```

Key: native `@property` returns domain objects (`Lamport`, `TokenAmount`, `Pubkey`) — not raw `int`/`str`. This means the Type doesn't need conversion logic.

### Type pattern

```python
class LocalCurveType(TypeBase[LocalCurve]):
    # Constructors
    @classmethod
    def from_dict(cls, d: object) -> LocalCurveValue:
        return LocalCurveValue(FuncCallOp(LocalCurve.from_dict, d))

    # Serialization
    def to_dict(self) -> DictValue:
        return DictValue(MethodCallOp(self, "to_dict"))

    # Methods → MethodCallOp
    def apply_buy(self, sol_in: object) -> LocalCurveValue:
        return LocalCurveValue(MethodCallOp(self, "apply_buy", sol_in))

    # Properties → GetAttrOp, wrap in domain Value directly (no conversion needed)
    @property
    def virtual_sol_reserves(self) -> LamportValue:
        return LamportValue(GetAttrOp(self, "virtual_sol_reserves"))

    @property
    def price_lamports(self) -> LamportValue:
        return LamportValue(GetAttrOp(self, "price_lamports"))
```

Since the native `@property` already returns a `Lamport`, `GetAttrOp` resolves to `Lamport` at runtime, and `LamportValue(...)` wraps it directly — no `from_int` conversion needed.

### Ref pattern (dict-stored)

```python
class LocalCurveRef(pv.ItemRef[dict, LocalCurveValue], LocalCurveType):
    def set(self, value: Arg[LocalCurve | dict]) -> LocalCurveValue:
        if isinstance(value, Term):
            val = MethodCallOp(value, "to_dict")      # deferred serialization
        elif isinstance(value, LocalCurve):
            val = value.to_dict()                      # immediate serialization
        else:
            val = value                                # raw dict passthrough
        return LocalCurveValue(ItemSetCmd(self, ensure_term(val)))

    def result(self, op: Term) -> object:
        return LocalCurveValue(FuncCallOp(LocalCurve.from_dict, op))
```

The `result()` hook deserializes on read (`dict` → `LocalCurve`). Call `.get()` to go through it — using the ref directly as a term resolves to raw `dict`.

## Capability Bases Reference

Choose which bases to inherit depending on what your type supports:

| Base | Gives you | Use when |
|------|-----------|----------|
| `EqualableBase` | `==`, `!=` | Type supports equality |
| `ComparableBase` | `==`, `!=`, `<`, `>`, `<=`, `>=` | Type is orderable |
| `TypeBase[T]` | Core type machinery | Always required |

For numeric types, add arithmetic:

| Base | Gives you |
|------|-----------|
| `Numeric` | `+`, `-`, `*`, `/`, `//`, `%`, `**`, `-unary` |
| `Logical` | `&`, `|`, `~`, `and_()`, `or_()`, `not_()` |
| `Bitwise` | `&`, `|`, `^`, `<<`, `>>` |

## Operation Wrappers Reference

| Wrapper | Use |
|---------|-----|
| `FuncCallOp(fn, *args)` | Call any Python function |
| `MethodCallOp(self, "method", *args)` | Call a method on the value |
| `AddOp(left, right)` | `left + right` |
| `SubOp(left, right)` | `left - right` |
| `MulOp(left, right)` | `left * right` |
| `DivOp(left, right)` | `left / right` |
| `EqOp(left, right)` | `left == right` |
| `LtOp(left, right)` | `left < right` |
| `ToStrOp(value)` | `str(value)` |
| `ToIntOp(value)` | `int(value)` |
| `ToFloatOp(value)` | `float(value)` |

## Full Example: Datetime Type

See `examples/example_arb_ref.py` for a complete datetime type with:

- `DatetimeType` with `from_timestamp()`, `from_iso()`, `to_timestamp()`, `__add__()`
- `DatetimeValue(ValueBase, DatetimeType)`
- `DatetimeRefBase(ItemRef, DatetimeType)` with `get()`/`set()`
- `PVDatetimeRef` and `DictDatetimeRef` substrate refs
- Mixed-substrate usage (PV + dict in one tree)
