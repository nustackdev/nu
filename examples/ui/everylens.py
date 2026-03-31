"""EveryLense example."""

from __future__ import annotations

import logging

from virtuals.views import DictView

import nu_virtuals as ebv
from nu.shape import Shape


logging.basicConfig(level=logging.INFO)


class Doc(Shape):
    input_text = ebv.StrRef.slot()
    output_text = ebv.StrRef.slot()
    num = ebv.IntRef.slot()


if __name__ == "__main__":
    from everylens import run_ui
    from virtuals.tkv.codecs import BinaryCodec, NoOpCodec
    from virtuals.tkv.observers.mem import InMemoryObserver
    from virtuals.tkv.storages.rocksdb import RocksDBStorage

    observer = InMemoryObserver(codec=NoOpCodec())
    observer.connect()
    storage = RocksDBStorage(codec=BinaryCodec(), path=".db-test", observer=observer)
    storage.open()

    with storage.transaction() as tx:
        root = DictView.open_root(tx)

    run_ui(Doc, storage, port=8080)
