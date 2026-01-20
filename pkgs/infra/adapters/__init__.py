"""Adapters for everybase.

Import directly from submodules:

    # Storage backends
    from everybase.adapters.storages.rocksdb import RocksDBStorage
    from everybase.adapters.storages.textdb import TextStorage
    from everybase.adapters.storages.inmemdb import InMemoryStorage

    # Codecs
    from everybase.adapters.codecs import BinaryCodec, TextCodec, NoOpCodec
    from everybase.adapters.codecs import BinaryKeyCodec, StringKeyCodec
    from everybase.adapters.codecs.json import JSONCodec
    from everybase.adapters.codecs.msgpack import MessagePackCodec
    from everybase.adapters.codecs.micropack import MicroPackCodec
    from everybase.adapters.codecs.pickle import PickleCodec
    from everybase.adapters.codecs.passthrough import PassthroughCodec

    # Observers
    from everybase.adapters.observers.in_memory import InMemoryObserver
    from everybase.adapters.observers.redis_pubsub import RedisObserver
"""
