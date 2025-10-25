import unittest

import rwrocks


class TestFilterPolicy(rwrocks.interfaces.FilterPolicy):
    def create_filter(self, keys) -> bytes:
        return b"nix"

    def key_may_match(self, key, fil) -> bool:
        return True

    def name(self) -> bytes:
        return b"testfilter"


class TestMergeOperator(rwrocks.interfaces.MergeOperator):
    def full_merge(self, *args, **kwargs):
        return (False, None)

    def partial_merge(self, *args, **kwargs):
        return (False, None)

    def name(self) -> bytes:
        return b"testmergeop"


class TestOptions(unittest.TestCase):
    #  def test_default_merge_operator(self):
    #  opts = rocksdb.Options()
    #  self.assertEqual(True, opts.paranoid_checks)
    #  opts.paranoid_checks = False
    #  self.assertEqual(False, opts.paranoid_checks)

    #  self.assertIsNone(opts.merge_operator)
    #  opts.merge_operator = "uint64add"
    #  self.assertIsNotNone(opts.merge_operator)
    #  self.assertEqual(opts.merge_operator, "uint64add")
    #  with self.assertRaises(TypeError):
    #  opts.merge_operator = "not an operator"

    # FIXME: travis test should include the latest version of rocksdb
    #  def test_compaction_pri(self):
    #  opts = rocksdb.Options()
    # default compaction_pri
    #  self.assertEqual(opts.compaction_pri, rocksdb.CompactionPri.by_compensated_size)
    #  self.assertEqual(opts.compaction_pri, rocksdb.CompactionPri.min_overlapping_ratio)
    #  opts.compaction_pri = rocksdb.CompactionPri.by_compensated_size
    #  self.assertEqual(opts.compaction_pri, rocksdb.CompactionPri.by_compensated_size)
    #  opts.compaction_pri = rocksdb.CompactionPri.oldest_largest_seq_first
    #  self.assertEqual(opts.compaction_pri, rocksdb.CompactionPri.oldest_largest_seq_first)
    #  opts.compaction_pri = rocksdb.CompactionPri.min_overlapping_ratio
    #  self.assertEqual(opts.compaction_pri, rocksdb.CompactionPri.min_overlapping_ratio)

    def test_enable_write_thread_adaptive_yield(self) -> None:
        opts = rwrocks.Options()
        self.assertEqual(opts.enable_write_thread_adaptive_yield, True)
        opts.enable_write_thread_adaptive_yield = False
        self.assertEqual(opts.enable_write_thread_adaptive_yield, False)

    def test_allow_concurrent_memtable_write(self) -> None:
        opts = rwrocks.Options()
        self.assertEqual(opts.allow_concurrent_memtable_write, True)
        opts.allow_concurrent_memtable_write = False
        self.assertEqual(opts.allow_concurrent_memtable_write, False)

    def test_compression_opts(self) -> None:
        opts = rwrocks.Options()
        compression_opts = opts.compression_opts
        # default value
        self.assertEqual(isinstance(compression_opts, dict), True)
        self.assertEqual(compression_opts["window_bits"], -14)
        # This doesn't match rocksdb latest
        # self.assertEqual(compression_opts['level'], -1)
        self.assertEqual(compression_opts["strategy"], 0)
        self.assertEqual(compression_opts["max_dict_bytes"], 0)

        with self.assertRaises(TypeError):
            opts.compression_opts = list(1, 2)

        opts.compression_opts = {"window_bits": 1, "level": 2, "strategy": 3, "max_dict_bytes": 4}
        compression_opts = opts.compression_opts
        self.assertEqual(compression_opts["window_bits"], 1)
        self.assertEqual(compression_opts["level"], 2)
        self.assertEqual(compression_opts["strategy"], 3)
        self.assertEqual(compression_opts["max_dict_bytes"], 4)

    def test_simple(self) -> None:
        opts = rwrocks.Options()
        self.assertEqual(True, opts.paranoid_checks)
        opts.paranoid_checks = False
        self.assertEqual(False, opts.paranoid_checks)

        self.assertIsNone(opts.merge_operator)
        ob = TestMergeOperator()
        opts.merge_operator = ob
        self.assertEqual(opts.merge_operator, ob)

        self.assertIsInstance(opts.comparator, rwrocks.BytewiseComparator)

        self.assertIn(
            opts.compression,
            (rwrocks.CompressionType.no_compression, rwrocks.CompressionType.snappy_compression),
        )

        opts.compression = rwrocks.CompressionType.zstd_compression
        self.assertEqual(rwrocks.CompressionType.zstd_compression, opts.compression)

    def test_block_options(self) -> None:
        rwrocks.BlockBasedTableFactory(
            block_size=4096, filter_policy=TestFilterPolicy(), block_cache=rwrocks.LRUCache(100)
        )

    def test_unicode_path(self) -> None:
        name = b"/tmp/M\xc3\xbcnchen".decode("utf8")
        opts = rwrocks.Options()
        opts.db_log_dir = name
        opts.wal_dir = name

        self.assertEqual(name, opts.db_log_dir)
        self.assertEqual(name, opts.wal_dir)

    def test_table_factory(self) -> None:
        opts = rwrocks.Options()
        self.assertIsNone(opts.table_factory)

        opts.table_factory = rwrocks.BlockBasedTableFactory()
        opts.table_factory = rwrocks.PlainTableFactory()

    def test_compaction_style(self) -> None:
        opts = rwrocks.Options()
        self.assertEqual("level", opts.compaction_style)

        opts.compaction_style = "universal"
        self.assertEqual("universal", opts.compaction_style)

        opts.compaction_style = "level"
        self.assertEqual("level", opts.compaction_style)

        assertRaisesRegex = self.assertRaisesRegex

        with assertRaisesRegex(Exception, "Unknown compaction style"):
            opts.compaction_style = "foo"

    def test_compaction_opts_universal(self) -> None:
        opts = rwrocks.Options()
        uopts = opts.compaction_options_universal
        self.assertEqual(-1, uopts["compression_size_percent"])
        self.assertEqual(200, uopts["max_size_amplification_percent"])
        self.assertEqual("total_size", uopts["stop_style"])
        self.assertEqual(1, uopts["size_ratio"])
        self.assertEqual(2, uopts["min_merge_width"])
        self.assertGreaterEqual(4294967295, uopts["max_merge_width"])

        new_opts = {"stop_style": "similar_size", "max_merge_width": 30}
        opts.compaction_options_universal = new_opts
        uopts = opts.compaction_options_universal

        self.assertEqual(-1, uopts["compression_size_percent"])
        self.assertEqual(200, uopts["max_size_amplification_percent"])
        self.assertEqual("similar_size", uopts["stop_style"])
        self.assertEqual(1, uopts["size_ratio"])
        self.assertEqual(2, uopts["min_merge_width"])
        self.assertEqual(30, uopts["max_merge_width"])

    def test_row_cache(self) -> None:
        opts = rwrocks.Options()
        self.assertIsNone(opts.row_cache)
        opts.row_cache = cache = rwrocks.LRUCache(2 * 1024 * 1024)
        self.assertEqual(cache, opts.row_cache)
