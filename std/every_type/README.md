# every_type

Extended type refs for everybase - refs for Decimal, UUID, datetime, Path, and more.

## Types

### Numeric
- **DecimalRef** - Arbitrary precision decimal arithmetic
- **FractionRef** - Exact rational number arithmetic
- **ComplexRef** - Complex number operations
- **BasisPointRef** - Basis points (1/100 of a percent)
- **PercentageRef** - Percentage values

### Datetime
- **DateRef** - Calendar dates
- **DatetimeRef** - Date and time
- **TimeRef** - Time of day
- **TimedeltaRef** - Duration/time differences
- **TimezoneRef** - Timezone information

### Other
- **PathRef** - Filesystem paths
- **UUIDRef** - Universally unique identifiers

## Usage

```python
from every_type import DecimalRef, UUIDRef
from every_type.pv import PVDecimalRef, DecimalSlot

# Python memory ref
d = DecimalRef.from_str("123.456")
result = d + DecimalRef.from_str("0.001")

# PV storage in Shape
from every import Shape

class Account(Shape):
    balance: PVDecimalRef = DecimalSlot()
    id: PVUUIDRef = UUIDSlot()
```

## Structure

```
every_type/
├── src/every_type/
│   ├── *_ref.py      # RefBase classes (DecimalRefBase, etc.)
│   ├── *_cls.py      # Custom Python classes (BasisPoint, Percentage)
│   ├── args.py       # Type aliases for arguments
│   ├── py/           # Python memory refs
│   │   └── refs.py   # DecimalRef, UUIDRef, etc.
│   └── pv/           # PV storage refs
│       ├── refs.py   # PVDecimalRef, PVUUIDRef, etc.
│       └── slots.py  # DecimalSlot, UUIDSlot, etc.
└── tests/
    ├── unit/         # Unit tests
    └── functional/   # Functional tests with storage
```

## Architecture

Each type follows the ref system pattern:

1. **RefBase** (e.g., `DecimalRefBase`) - Abstract base with type operations, inherits from traits
2. **PyRef** (e.g., `DecimalRef`) - Python memory ref, combines `PyRefBase[T]` + `*RefBase`
3. **PVRef** (e.g., `PVDecimalRef`) - PV storage ref with get/set serialization
4. **Slot** (e.g., `DecimalSlot`) - Factory for creating PV refs in Shape fields
