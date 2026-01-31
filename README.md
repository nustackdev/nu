# everybase

Term Programming platform for Python.

## Packages

| Package | Description |
|---------|-------------|
| `every` | Core protocols - Term, Flow, Ref, Sentinel |
| `everybase` | Base implementations - Python types, computations |

### Standard Library (std/)

| Package | Description |
|---------|-------------|
| `every_datetime` | Date, Time, DateTime, Timezone types |
| `every_numeric` | Decimal, Fraction, Percentage types |
| `every_uuid` | UUID type |
| `every_path` | Path type |

### Extensions (pkgs/)

| Package | Description |
|---------|-------------|
| `every_notion` | Notion API integration |
| `every_dict` | Dict substrate (plain nested dicts, no persistence) |

## Install

```bash
pip install every everybase
```

## Quick Start

```python
from every import Term, Ref, Flow
from everybase.types import IntType, StrType
```

## Development

```bash
# Setup
make sync

# Test
make test

# Lint
make format
```

See [contributing/](contributing/) for detailed docs.

## Structure

```
abc/          # Core packages
├── every/    # Protocols
└── everybase/  # Base implementations

std/          # Standard library
pkgs/         # Extensions
```

## License

MIT
