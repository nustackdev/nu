# e/ Package Architecture

## Overview

The `e` package is a single Python namespace containing all components of the Term Programming platform. Everything is accessible via `e.<component>`.

## Structure

```
src/e/
│
├── __init__.py                         # Exports core protocols
│
│   PROTOCOLS (stable abstractions - the three topologies)
│
├── term/                               # Data topology - Term algebra
│   ├── __init__.py
│   ├── ops/                            # Operations (arithmetic, comparison, etc.)
│   ├── types/                          # Type implementations (IntType, StrType, etc.)
│   ├── shape/                          # Shape definitions
│   └── tests/
│
├── flow/                               # Execution topology - Flow algebra
│   ├── __init__.py
│   ├── runtime/                        # Runtime, Services
│   └── tests/
│
├── link/                               # Network topology - Link algebra
│   ├── __init__.py
│   └── tests/
│
│   FABRICS (domain-specific Term vocabularies)
│
├── kv/                                 # KV Fabric - storage views
│   ├── __init__.py
│   ├── view.py
│   ├── storage.py
│   ├── container.py
│   └── tests/
│
├── chat/                               # Chat Fabric (future)
├── notion/                             # Notion Fabric (future)
├── solana/                             # Solana Fabric (future)
│
│   TYPES (stdlib-like value implementations)
│
├── datetime/
├── decimal/
├── path/
├── uuid/
├── complex/
├── fraction/
└── ...
```

## Design Principles

### 1. Flat Namespace
Everything is `e.<component>`. No deep nesting like `e.proto.term` or `e.fabric.kv`.

### 2. Co-located Tests
Each component has its own `tests/` directory. This keeps tests coupled with code as the number of components grows.

### 3. Protocol vs Implementation
The distinction is by convention, not structure:
- **Protocols**: `term`, `flow`, `link` (the three topologies - stable abstractions)
- **Fabrics**: `kv`, `chat`, `notion`, `solana` (domain vocabularies)
- **Types**: `datetime`, `path`, `decimal` (stdlib-like implementations)

### 4. Single Package
One `pyproject.toml`, one installable package. No multi-package coordination.

## Usage

```python
# Core protocols (re-exported at top level)
from e import Term, Flow, Link

# Protocol details
from e.term import Ref, Value, Op, Shape
from e.term.ops import AddOp, MulOp
from e.term.types import IntType, StrType
from e.flow import Runtime, Services
from e.link import Node

# Fabrics
from e.kv import View, Storage, Container
from e.chat import Message, Thread          # future
from e.notion import Page, Block            # future

# Types
from e.datetime import DateTime, Date, Time
from e.decimal import Decimal
from e.path import Path
```

## Adding New Components

Use the Makefile target:

```bash
make new-pkg name=redis
```

This creates:
```
e/redis/
├── __init__.py
└── tests/
    ├── __init__.py
    └── conftest.py
```

## Test Discovery

pytest is configured to discover all `**/tests/` directories:

```toml
[tool.pytest.ini_options]
testpaths = ["e"]
python_files = ["test_*.py"]
```

Run all tests: `make test`
Run specific component: `pytest e/term/tests -v`
