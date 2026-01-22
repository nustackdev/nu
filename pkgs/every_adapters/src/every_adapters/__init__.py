"""Adapters for everybase.

Import directly from submodules:

    # Storage backends
    from every_adapters.storages.rocksdb import RocksDBStorage
    from every_adapters.storages.textdb import TextStorage
    from every_adapters.storages.inmemdb import InMemoryStorage

    # Codecs
    from every_adapters.codecs import BinaryCodec, TextCodec, NoOpCodec
    from every_adapters.codecs import BinaryKeyCodec, StringKeyCodec
    from every_adapters.codecs.json import JSONCodec
    from every_adapters.codecs.msgpack import MessagePackCodec
    from every_adapters.codecs.micropack import MicroPackCodec
    from every_adapters.codecs.pickle import PickleCodec
    from every_adapters.codecs.passthrough import PassthroughCodec

    # Observers
    from every_adapters.observers.in_memory import InMemoryObserver
    from every_adapters.observers.redis_pubsub import RedisObserver

    # Storage presets
    from every_adapters.storage import text_storage, rocksdb_storage, rocksdb_storage_inmemory
"""
