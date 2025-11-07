# content of test_sample.py
import shutil
import tempfile
from pathlib import Path

import rwrocks


def test_open_skiplist_memtable_factory() -> None:
    opts = rwrocks.Options()
    opts.memtable_factory = rwrocks.SkipListMemtableFactory()
    opts.create_if_missing = True

    loc = tempfile.mkdtemp()
    try:
        rwrocks.DB(str(Path(loc) / "test"), opts)
    finally:
        shutil.rmtree(loc)


def test_open_vector_memtable_factory() -> None:
    opts = rwrocks.Options()
    opts.allow_concurrent_memtable_write = False
    opts.memtable_factory = rwrocks.VectorMemtableFactory()
    opts.create_if_missing = True
    loc = tempfile.mkdtemp()
    try:
        rwrocks.DB(str(Path(loc) / "test"), opts)
    finally:
        shutil.rmtree(loc)
