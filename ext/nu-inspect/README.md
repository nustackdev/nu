# nu-inspect

Inspection tools for Nu trees and Shapes.

## Install

```bash
pip install nu-inspect
```

## Usage

```python
from nu_inspect import render_nu, render_shape, annotate_steps, annotate_retries

# Render a Nu tree as an ANSI-colored tree (default)
print(render_nu(nu))

# Plain text, no color — for logs/files
print(render_nu(nu, as_="plain"))

# Interactive HTML explorer — save and open yourself
from pathlib import Path
Path("tree.html").write_text(render_nu(nu, as_="html"))

# Render a Shape + storage as an ANSI tree
print(render_shape(Market, storage))
print(render_shape(Market, storage, as_="plain"))

# Execution trace: wrap a tree with logging hooks
traced = annotate_steps(annotate_retries(tree))
```

## API

- `render_nu(nu, *, as_="ansi")` — `"ansi"`, `"plain"`, `"html"`
- `render_shape(shape_cls, storage, *, as_="ansi", max_items=20, max_depth=10, max_str=80)` — `"ansi"`, `"plain"`
- `annotate_steps(tree)` — wraps sequential children in step-tracking spans
- `annotate_retries(tree)` — adds log hooks to Retry nodes
- `set_logger_name(tree, name)` — rename logger on all Log nodes
