from libc.stddef cimport size_t
from libc.stdint cimport int64_t, uint32_t, uint64_t
from libcpp cimport bool as cpp_bool
from libcpp.string cimport string
from libcpp.vector cimport vector

from rwrocks.iterator cimport Iterator
from rwrocks.slice_ cimport Slice
from rwrocks.snapshot cimport Snapshot
from rwrocks.status cimport Status
from rwrocks.std_memory cimport shared_ptr

cimport rwrocks.db as db
cimport rwrocks.options as options


cdef extern from "rocksdb/utilities/transaction_db_mutex.h" namespace "rocksdb":
    cdef cppclass TransactionDBMutexFactory:
        pass


cdef extern from "rocksdb/utilities/transaction_db.h" namespace "rocksdb":
    ctypedef uint64_t TransactionID
    ctypedef string TransactionName

    cdef enum TxnDBWritePolicy:
        WRITE_COMMITTED
        WRITE_PREPARED
        WRITE_UNPREPARED

    cdef cppclass LockManager:
        pass

    cdef cppclass LockManagerHandle:
        LockManager* getLockManager() nogil except+

    cdef cppclass TransactionDBOptions:
        TransactionDBOptions() nogil except+
        int64_t max_num_locks
        uint32_t max_num_deadlocks
        size_t num_stripes
        int64_t transaction_lock_timeout
        int64_t default_lock_timeout
        shared_ptr[TransactionDBMutexFactory] custom_mutex_factory
        TxnDBWritePolicy write_policy
        cpp_bool rollback_merge_operands
        shared_ptr[LockManagerHandle] lock_mgr_handle
        cpp_bool skip_concurrency_control
        int64_t default_write_batch_flush_threshold

    cdef cppclass TransactionDBWriteOptimizations:
        TransactionDBWriteOptimizations() nogil except+
        cpp_bool skip_concurrency_control
        cpp_bool skip_duplicate_key_check

    cdef cppclass TransactionOptions:
        TransactionOptions() nogil except+
        cpp_bool set_snapshot
        cpp_bool deadlock_detect
        cpp_bool use_only_the_last_commit_time_batch_for_recovery
        int64_t lock_timeout
        int64_t expiration
        int64_t deadlock_detect_depth
        size_t max_write_batch_size
        cpp_bool skip_concurrency_control
        cpp_bool skip_prepare
        int64_t write_batch_flush_threshold

    cdef cppclass Transaction:
        Status Commit() nogil except+
        Status Rollback() nogil except+
        Status Prepare() nogil except+
        void SetSnapshot() nogil except+
        const Snapshot* GetSnapshot() const nogil except+
        void ClearSnapshot() nogil except+
        Status SetName(const TransactionName&) nogil except+
        TransactionName GetName() const nogil except+
        TransactionID GetID() const nogil except+
        void SetSavePoint() nogil except+
        Status PopSavePoint() nogil except+
        Status RollbackToSavePoint() nogil except+
        void DisableIndexing() nogil except+
        void EnableIndexing() nogil except+
        Status Put(db.ColumnFamilyHandle*, const Slice&, const Slice&, cpp_bool assume_tracked = False) nogil except+
        Status Put(const Slice&, const Slice&) nogil except+
        Status Merge(db.ColumnFamilyHandle*, const Slice&, const Slice&, cpp_bool assume_tracked = False) nogil except+
        Status Merge(const Slice&, const Slice&) nogil except+
        Status Delete(db.ColumnFamilyHandle*, const Slice&, cpp_bool assume_tracked = False) nogil except+
        Status Delete(const Slice&) nogil except+
        Status SingleDelete(db.ColumnFamilyHandle*, const Slice&, cpp_bool assume_tracked = False) nogil except+
        Status SingleDelete(const Slice&) nogil except+
        Status Get(const options.ReadOptions&, db.ColumnFamilyHandle*, const Slice&, string*) nogil except+
        Status Get(const options.ReadOptions&, const Slice&, string*) nogil except+
        vector[Status] MultiGet(
            const options.ReadOptions&,
            const vector[db.ColumnFamilyHandle*]&,
            const vector[Slice]&,
            vector[string]*) nogil except+
        vector[Status] MultiGet(
            const options.ReadOptions&,
            const vector[Slice]&,
            vector[string]*) nogil except+
        Iterator* GetIterator(const options.ReadOptions&) nogil except+
        Iterator* GetIterator(const options.ReadOptions&, db.ColumnFamilyHandle*) nogil except+

    cdef cppclass TransactionDB(db.DB):
        Transaction* BeginTransaction(
            const options.WriteOptions&,
            const TransactionOptions&,
            Transaction* old_txn) nogil except+
        Transaction* BeginTransaction(
            const options.WriteOptions&,
            const TransactionOptions&) nogil except+
        Transaction* GetTransactionByName(const TransactionName&) nogil except+
        void GetAllPreparedTransactions(vector[Transaction*]*) nogil except+

    cdef Status TransactionDB_Open "rocksdb::TransactionDB::Open"(
        const options.Options&,
        const TransactionDBOptions&,
        const string&,
        TransactionDB**) nogil except+

    cdef Status TransactionDB_Open_CF "rocksdb::TransactionDB::Open"(
        const options.DBOptions&,
        const TransactionDBOptions&,
        const string&,
        const vector[db.ColumnFamilyDescriptor]&,
        vector[db.ColumnFamilyHandle*]*,
        TransactionDB**) nogil except+
