# content of test_sample.py
import os
import shutil
import tempfile

import rwrocks


def test_open_skiplist_memtable_factory():
    opts = rwrocks.Options()
    opts.memtable_factory = rwrocks.SkipListMemtableFactory()
    opts.create_if_missing = True

    loc = tempfile.mkdtemp()
    try:
        test_db = rwrocks.DB(os.path.join(loc, "test"), opts)
    finally:
        shutil.rmtree(loc)


def test_open_vector_memtable_factory():
    opts = rwrocks.Options()
    opts.allow_concurrent_memtable_write = False
    opts.memtable_factory = rwrocks.VectorMemtableFactory()
    opts.create_if_missing = True
    loc = tempfile.mkdtemp()
    try:
        test_db = rwrocks.DB(os.path.join(loc, "test"), opts)
    finally:
        shutil.rmtree(loc)
