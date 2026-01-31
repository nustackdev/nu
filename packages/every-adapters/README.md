# every-adapters

Storage, codec, and observer adapters for everybase.

## Install

```bash
pip install every-adapters
```

## Usage

```python
# Storage presets
from every_adapters.storage import text_storage, rocksdb_storage

# Codecs
from every_adapters.codecs import BinaryCodec, TextCodec
from every_adapters.codecs.json import JSONCodec

# Storage backends
from every_adapters.storages.rocksdb import RocksDBStorage
from every_adapters.storages.textdb import TextStorage

# Observers
from every_adapters.observers.in_memory import InMemoryObserver
from every_adapters.observers.redis_pubsub import RedisObserver
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=pkgs/every_adapters
```
