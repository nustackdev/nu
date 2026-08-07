---
title: Install
---

Install Nu from PyPI. For hacking on Nu itself, see [Install from source](install-from-source).

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

```bash
python -c "import nu; print(nu.__version__)"
```
