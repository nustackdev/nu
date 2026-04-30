# nu-mem

Nu Shapes fabric adapter for in-memory state. Plain nested Python dicts as the data bag — no storage backend, no views, no reactivity.

## Usage

```python
import nu_mem as nm
from nu import Context
from nu.shapes import Shape

class User(Shape):
    name = nm.StrRef.slot()
    age = nm.IntRef.slot()

data = {}
ctx = Context().bind(data, dict, User)
```

## Development

Part of the [Nu](https://github.com/nustackdev/nu) workspace.
