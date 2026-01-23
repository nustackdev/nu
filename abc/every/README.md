# every

Core primitives for the every ecosystem.

## Installation

```bash
pip install every
```

Or with uv:

```bash
uv add every
```

## Overview

The `every` package provides foundational abstractions:

- **Term** - Computation expressions and references
- **Flow** - Execution runtime and paths
- **Sentinel** - Special marker values (NotSet, Empty, Invalid)
- **Arg** - Type-safe argument definitions

## Usage

```python
from every import Term, Ref, Flow
```

## Development

This package is part of the [everybase monorepo](https://github.com/everyabc/everybase).

```bash
# From repo root
make test-pkg PKG=abc/every
```
