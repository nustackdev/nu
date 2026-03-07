# eb-shape-lens

Terminal data viewer for everybase Shapes.

## Installation

```bash
pip install eb-shape-lens
```

## Usage

```python
from eb_shape_lens import print_shape

# Shape class + backing storage dict
print_shape(Market, storage)
```

To get the string directly:

```python
from eb_shape_lens import format_shape

text = format_shape(Market, storage, color=False)
```

## Example output

```
Market
├── misc_val int: 42
├── signals dict[str, float]: {'vix': 23.5, 'sentiment': 0.75}
├── prices list[float]: [100.5, 101.2, 99.8]
├── symbols dict[str, SymbolInfo] (2 items)
│  ├── 'AAPL': SymbolInfo
│  │  ├── price float: 150.25
│  │  ├── volume int: 1000000
│  │  └── exchange str: 'NASDAQ'
│  └── 'GOOGL': SymbolInfo
│     ├── price float: 2800.0
│     ├── volume int: 500000
│     └── exchange str: 'NASDAQ'
├── orders list[Order] (2 items)
│  ├── [0] Order
│  │  ├── id str: 'ORD001'
│  │  ├── symbol str: 'AAPL'
│  │  ├── quantity int: 100
│  │  └── price float: 150.0
│  └── [1] Order
│     ├── id str: 'ORD002'
│     ├── symbol str: 'GOOGL'
│     ├── quantity int: 50
│     └── price float: 2800.0
└── last_order: Order
   ├── id str: 'ORD-LAST'
   ├── symbol str: 'BTC'
   ├── quantity int: 1
   └── price float: 99999.0
```

Type annotations (dim) are derived from slot metadata — ref type + kwargs.

## Options

- `color` — ANSI escape codes (default `True`)
- `max_items` — items shown per collection before truncation (default `20`)
- `max_depth` — max nesting depth (default `10`)
- `max_str` — max string value length before truncation (default `80`)
