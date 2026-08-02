---
title: Hello, Nu
---

Run your first Nu program: a tree that prints "hello" once a second.

Install Nu first: see [Install](../how-to/install).

```python
import asyncio
import nu

tree = nu.ForeverDo(nu.print("hello") >> nu.Delay(1.0))

asyncio.run(nu.arun(tree))
```

Save as `hello.py`, then run:

```bash
python hello.py
```

You see "hello" print once a second, forever. Press Ctrl+C to stop.

```
hello
hello
hello
```

## What just happened

You built a tree of three Nu operations: `ForeverDo` loops its body, `print` writes a line, `Delay` waits. Nothing ran while you built it. `nu.arun` executed the tree.

`>>` composes left to right. So each loop iteration prints, then waits a second, then goes again.

That is the whole Nu model in miniature. You describe a tree, Nu runs it.

## Next

Add state and a browser dashboard: [Your first app](./your-first-app).
