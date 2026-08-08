---
title: Hello, Nu
---

Run your first Nu program: a tree that prints "Hello, Nu!" once.

Install Nu first: see [Install](../how-to/install).

```python
import nu

nu.run(nu.print("Hello, Nu!"))
```

Save as `hello.py`, then run:

```bash
python hello.py
```

You see:

```
Hello, Nu!
```

## What just happened

You built a tree of one Nu operation: `nu.print("Hello, Nu!")` describes a print. Nothing ran while you built it. `nu.run` executed the tree.

That is the whole Nu model in miniature. You describe a tree, Nu runs it.

## Next

Add state and a browser dashboard: [Your first app](./your-first-app).
