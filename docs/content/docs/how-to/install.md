---
title: Install
---

Python 3.12 or later.

```bash
pip install nu[minimal]      # core language only
pip install nu[default]      # + virtuals, RocksDB, type extensions
pip install nu[nudle]        # + UI fabric
pip install nu[distributed]  # + Ray + invisibles
```

Pick `default` unless you know you want less. Pick `nudle` when you want a browser tab as a Fabric. Pick `distributed` when the program spans machines.
