---
title: Install
---

Install Nu from PyPI. For hacking on Nu itself, see [Install from source](install-from-source). For editable dev across the full nustack (nu + virtuals + invisibles), see [Cross-repo dev](cross-repo-dev).

## Prerequisites

- Python 3.10 or later.

## Install

The everything-included install:

```bash
pip install "nustack-py[all]"
```

For a lean install, pick the extras you need instead of `[all]`. One extra per fabric, name matches the import path: `[virtuals]`, `[mem]`, `[ui]`, `[ray]`, `[invisibles]`.

```bash
pip install "nustack-py[mem,ui]"
```

## Verify

Check the install:

```bash
python -c "import nu; print(nu.__version__)"
```

Run the bundled counter demo. A live counter renders in a browser dashboard and persists across restarts:

```bash
nu demo counter
```

Open the browser tab that pops up. Kill the process, run it again, it picks up where it left off. `nu demo` shows all bundled demos.

Next: [Hello, Nu](../tutorials/hello) for your first program, or [Your first app](../tutorials/your-first-app) for a full walkthrough.
