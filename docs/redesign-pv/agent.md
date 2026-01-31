# Redesign Agent Guide

This is the entry point for agents implementing the everybase/every_pv redesign.
Read the design docs in this directory first, then use this file for
implementation guidance.

## Design Docs (read in order)

1. `01-vision.md` — Why: PV views have pythonic interfaces, everybase ops
   should work on them directly. Remove duplication from every_pv.
2. `02-workflow.md` — Workflow plan

## Codebase Map

### everyabc — abstract computation protocol
```
abc/everyabc/src/everyabc/
```

### everybase — toolbox: types + values + capabilities + morphisms
```
abc/everybase/src/everybase/
```

### every_pv — PV storage substrate
```
std/every_pv/src/every_pv/
```

### every_view — standard view implementations (NO CHANGES)
```
std/every_view/src/every_view/
  (DictView, ListView, SetView, etc. — unchanged)
```

### Reference: original PV library
```
/Users/gor/Projects/everyabc/pv/
  (read-only reference — the upstream PV library every_pv is based on)
```

## Implementation Phases

Execute in order. Each phase should leave tests passing before moving on.

Check out the wokflow.

## Verification Commands

```bash
# everybase tests
make test-pkg PKG=abc/everybase

# every_pv tests
make test-pkg PKG=std/every_pv
```

## Style Notes

- Python 3.10+, ruff for linting (rules in root pyproject.toml)
- No backwards compatibility — break whatever needed
- Never commit as Claude, never mention Claude as co-author
- Check contributing guidelines in ./contributing
- Check docs in ./docs for overall concepts
