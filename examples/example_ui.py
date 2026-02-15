"""EveryLense example."""

from __future__ import annotations

import logging

import eb_pv as pv
from eb_pv.views import DictView
from eb_shape import Shape


logging.basicConfig(level=logging.INFO)


class Doc(Shape):
    input_text = pv.StrRef.slot()
    output_text = pv.StrRef.slot()
    num = pv.IntRef.slot()


if __name__ == "__main__":
    from everylens import run_ui
    from tkv.codecs import BinaryCodec, NoOpCodec
    from tkv.observers.mem import InMemoryObserver
    from tkv.storages.rocksdb import RocksDBStorage

    observer = InMemoryObserver(codec=NoOpCodec())
    observer.connect()
    storage = RocksDBStorage(codec=BinaryCodec(), path=".db-test", observer=observer)
    storage.open()

    with storage.transaction() as tx:
        root = DictView.open_root(tx)

    run_ui(Doc, storage, port=8080)
