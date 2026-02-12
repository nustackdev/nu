# eb-tree-view

Interactive HTML tree explorer for everybase.

## Installation

```bash
pip install eb-tree-view
```

## Usage

```python
from eb_tree_view import open_in_browser

# any everybase tree node
open_in_browser(tree)
```

This writes a self-contained HTML file to a temp directory and opens it in the default browser.

To get the HTML string directly:

```python
from eb_tree_view import render_html

html = render_html(tree, title="my tree")
```

## Features

- Dark devtools-inspired theme (VS Code / Chrome DevTools palette)
- Expand/collapse with chevrons, double-click, or arrow keys
- Keyboard navigation (up/down/left/right)
- Node detail panel with type, category, attributes, and breadcrumb trail
- Real-time search with auto-expand and match highlighting
- Purity indicators for morphism nodes
- Stats bar with node count, depth, and category breakdown
- Zero external dependencies — single self-contained HTML file
