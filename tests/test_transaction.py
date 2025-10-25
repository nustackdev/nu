import gc
import os
import shutil
import tempfile
import unittest

import rwrocks


class TransactionTestHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.db_loc = tempfile.mkdtemp()
        self.addCleanup(self._cleanup_db)

    def _cleanup_db(self) -> None:
        if hasattr(self, "db"):
            del self.db
        gc.collect()
        if os.path.exists(self.db_loc):
            shutil.rmtree(self.db_loc)


class TestTransactionDB(TransactionTestHelper):
    def setUp(self) -> None:
        super().setUp()
        opts = rwrocks.Options(create_if_missing=True)
        self.txn_opts = rwrocks.TransactionDBOptions()
        self.db = rwrocks.TransactionDB(
            os.path.join(self.db_loc, "txn"),
            opts,
            txn_db_opts=self.txn_opts,
        )

    def test_commit_persists_changes(self) -> None:
        txn = self.db.begin_transaction()
        txn.put(b"a", b"1")
        txn.commit()
        txn.close()
        self.assertEqual(self.db.get(b"a"), b"1")

    def test_rollback_discards_changes(self) -> None:
        txn = self.db.begin_transaction()
        txn.put(b"a", b"1")
        txn.rollback()
        txn.close()
        self.assertIsNone(self.db.get(b"a"))

    def test_savepoint_and_rollback(self) -> None:
        txn = self.db.begin_transaction()
        txn.put(b"a", b"1")
        txn.save_point()
        txn.put(b"b", b"2")
        txn.rollback_to_save_point()
        txn.commit()
        txn.close()

        self.assertEqual(self.db.get(b"a"), b"1")
        self.assertIsNone(self.db.get(b"b"))

    def test_transaction_iterators_include_uncommitted(self) -> None:
        txn = self.db.begin_transaction()
        txn.put(b"a", b"1")
        txn.put(b"b", b"2")

        it = txn.iteritems()
        it.seek_to_first()
        self.assertEqual(it.get(), (b"a", b"1"))
        it.seek(b"b")
        self.assertEqual(it.get(), (b"b", b"2"))

        txn.rollback()
        txn.close()

    def test_multi_get_inside_transaction(self) -> None:
        txn = self.db.begin_transaction()
        txn.put(b"a", b"1")
        txn.put(b"b", b"2")

        result = txn.multi_get([b"a", b"b", b"missing"])
        self.assertEqual(result[b"a"], b"1")
        self.assertEqual(result[b"b"], b"2")
        self.assertIsNone(result[b"missing"])

        txn.commit()
        txn.close()

    def test_disable_enable_indexing_roundtrip(self) -> None:
        txn = self.db.begin_transaction()
        txn.disable_indexing()
        txn.enable_indexing()
        txn.rollback()
        txn.close()

    def test_named_transaction_metadata(self) -> None:
        txn = self.db.begin_transaction()
        txn.set_name("primary")
        self.assertTrue(txn.get_name().startswith("primary"))
        self.assertIsInstance(txn.get_id(), int)
        txn.rollback()
        txn.close()


class TestTransactionOptionsSemantics(unittest.TestCase):
    def test_write_policy_roundtrip(self) -> None:
        opts = rwrocks.TransactionDBOptions()
        opts.write_policy = rwrocks.TxnDBWritePolicy.write_prepared
        self.assertEqual(
            opts.write_policy,
            rwrocks.TxnDBWritePolicy.write_prepared,
        )

    def test_transaction_options_defaults(self) -> None:
        txn_opts = rwrocks.TransactionOptions()
        self.assertFalse(txn_opts.set_snapshot)
        txn_opts.set_snapshot = True
        self.assertTrue(txn_opts.set_snapshot)
