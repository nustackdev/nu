# eb-dict

Dict adapter for everybase. Plain Python dicts as data backend.

## Usage

```python
from eb_dict import IntRef, StrRef
from everybase import Context
from everybase.shape import Shape

class User(Shape):
    name = StrRef.slot()
    age = IntRef.slot()

data = {}
ctx = Context().bind(data, dict, User)
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).
