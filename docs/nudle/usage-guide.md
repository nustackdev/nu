# Usage Guide

everylens is a pip-installable package. You import it into your code, pass it a Shape and storage, and it runs a web UI for browsing and editing your data.

## Install

```bash
pip install everylens
```

## Instrument your code

```python
from everylens import run_ui
from eb_pv.views import DictView
from eb_shape import Shape
import eb_pv as pv
from tkv.codecs import NoOpCodec
from tkv.observers.mem import InMemoryObserver
from tkv.storages.mem import InMemoryStorage

# 1. Define your Shapes
class Config(Shape):
    app_name = pv.StrRef.slot()
    debug = pv.BoolRef.slot()
    max_retries = pv.IntRef.slot()

class App(Shape):
    config = pv.ShapeRef.slot(Config)
    version = pv.StrRef.slot()

# 2. Set up storage (any storage — InMemory, RocksDB, etc.)
observer = InMemoryObserver(codec=NoOpCodec())
observer.connect()
storage = InMemoryStorage(codec=NoOpCodec(), observer=observer)
storage.open()

# 3. Seed data
with storage.transaction() as tx:
    root = DictView.open_root(tx)
    config = root.open_child("config", DictView)
    config.store({"app_name": "myapp", "debug": True, "max_retries": 3})
    root["version"] = "1.0.0"

# 4. Run
run_ui(App, storage, port=8080)
```

Open `http://localhost:8080` — you get a live UI for your Shape tree.

## What you provide

- **Shape** — your data schema, defined as Python classes with typed slots
- **Storage** — any storage instance implementing the everybase `StorageProtocol` (InMemory, RocksDB, etc.)

## What everylens does

- Introspects your Shape to build a schema (slot names, types, nesting)
- Runs a FastAPI server with a WebSocket endpoint
- Serves a React frontend that renders your Shape generically
- On each request: re-constructs the Term tree, wraps in `Atomic` span, executes against your storage
- Storage boundaries (transactions, snapshots) are handled automatically — everylens never touches them directly
