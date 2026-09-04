"""One call that stands up a whole storage stack, in either of two forms.

A working KV fabric is six things bound together: a Codec, a Transport, a
Publisher, an Observer, a Storage and a Navigator. Writing that out by hand is
six lines that are the same six lines every time, in an order that matters,
with a ``publisher_type=`` on the Storage that has to agree with the Publisher
above it. The presets here are those lines, already correct, named after the
backend they stand up.

The ``*_navigator`` and ``*_observer`` functions return a ``With`` bracket
composed of ``Provide`` peers. It drops straight into a tree as the fabric a
program runs against, and being an ordinary bracket it gets bind order and
LIFO teardown for free::

    app = nu.With(nu.kv.rocksdb_navigator(".db"), body=program)

The ``*_storage`` functions are the other form: plain context managers handing
back a live ``StorageProtocol``, for wiring a Context by hand rather than
through the tree. The two forms are independent; neither is built on the other.

Every navigator preset takes ``tags``, folded onto both the Storage and the
Navigator binding. That is how a shard names itself: bind one preset per shard
under its own tag, and a Ref carrying that scope routes to it.

The ``_redis`` variants swap the in-process Publisher and Observer for Redis
ones, which is what makes change notifications cross process boundaries. The
plain variants keep everything in-process and need nothing running.

``inmem_observer`` and ``redis_observer`` bind the listening half alone, for an
actor that reacts to changes without owning a storage of its own.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from nu.context.fabric import With
    from virtuals.tkv.storage import StorageProtocol


__all__ = [
    "inmem_observer",
    "lmdb_navigator",
    "lmdb_navigator_redis",
    "lmdb_storage",
    "memory_navigator",
    "memory_storage",
    "redis_observer",
    "rocksdb_navigator",
    "rocksdb_navigator_redis",
    "rocksdb_storage",
    "rocksdb_storage_redis",
    "text_navigator",
    "text_storage",
]


@contextmanager
def memory_storage() -> Generator[StorageProtocol, None, None]:
    """Create in-memory storage with no-op codec and in-memory publisher.

    No persistence, no serialization: Python objects stored as-is.
    Useful for testing, prototyping, and ephemeral service handles.

    Yields:
        Configured in-memory storage instance
    """
    from virtuals.codecs import NoOpCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.mem import InMemoryStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        InMemoryStorage(
            codec=NoOpCodec(),
            publisher=publisher,
        ) as storage,
    ):
        yield storage


@contextmanager
def lmdb_storage(
    path: str,
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
) -> Generator[StorageProtocol, None, None]:
    """Create LMDB storage with binary codec and in-memory publisher.

    Args:
        path: Path to LMDB env (directory if subdir=True, file otherwise).
        read_only: Open the environment read-only.
        map_size: Maximum on-disk size in bytes. Default 10 GiB.
        max_readers: Maximum concurrent reader slots.
        subdir: If True, treat `path` as a directory; if False, as the env file.
        sync: If True, fsync data pages after each commit.

    Yields:
        Configured LMDB storage instance.
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.lmdb import LMDBStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        LMDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            map_size=map_size,
            max_readers=max_readers,
            subdir=subdir,
            sync=sync,
        ) as storage,
    ):
        yield storage


@contextmanager
def text_storage(path: str) -> Generator[StorageProtocol, None, None]:
    """Create text storage with text codec and in-memory publisher.

    Args:
        path: Path for text storage directory

    Yields:
        Configured text storage instance
    """
    from virtuals.codecs import TextCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.textdb import TextStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        TextStorage(
            path=path,
            codec=TextCodec(),
            publisher=publisher,
        ) as storage,
    ):
        yield storage


@contextmanager
def rocksdb_storage(
    path: str,
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and in-memory publisher.

    Args:
        path: Path to RocksDB database directory
        read_only: Open database in read-only mode
        secondary_path: Path to secondary RocksDB instance
        secondary_refresh_interval: Interval in seconds for background
            try_catch_up_with_primary on secondary DBs. None disables.

    Yields:
        Configured RocksDB storage instance
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.mem import InMemoryPublisher
    from virtuals.storages.rocksdb import RocksDBStorage
    from virtuals.tkv.transport import InMemoryTransport

    transport = InMemoryTransport()
    with (
        InMemoryPublisher(transport=transport) as publisher,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            secondary_path=secondary_path,
            secondary_refresh_interval=secondary_refresh_interval,
        ) as storage,
    ):
        yield storage


@contextmanager
def rocksdb_storage_redis(
    path: str,
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "__every__",
) -> Generator[StorageProtocol, None, None]:
    """Create RocksDB storage with binary codec and Redis publisher.

    Args:
        path: Path to RocksDB database directory
        read_only: Permissions
        secondary_path: Open as secondary rocksdb storage
        secondary_refresh_interval: Interval in seconds for background
            try_catch_up_with_primary on secondary DBs. None disables.
        redis_url: Redis service url
        channel_prefix: Redis channel prefix

    Yields:
        Configured RocksDB storage instance
    """
    from virtuals.codecs import BinaryCodec
    from virtuals.publishers.redis_pubsub import RedisPublisher
    from virtuals.storages.rocksdb import RocksDBStorage

    with (
        RedisPublisher(
            redis_url=redis_url,
            channel_prefix=channel_prefix,
        ) as publisher,
        RocksDBStorage(
            path=path,
            codec=BinaryCodec(),
            publisher=publisher,
            read_only=read_only,
            secondary_path=secondary_path,
            secondary_refresh_interval=secondary_refresh_interval,
        ) as storage,
    ):
        yield storage


# =========================================================================
# Bracket-form presets: drop into a ``nu.With(...)`` tree.
#
# Each factory returns a single ``With`` bracket that peers ``Provide``s the
# whole Codec + Transport + Publisher + Observer + Storage (+ Navigator)
# stack. Same order and LIFO teardown as a hand-written
# ``With(Provide(Codec, ...), Provide(InMemoryTransport, ...), ...)``.
#
# ``tags=`` folds onto both the Storage and Navigator bindings so a shard
# picks its storage via ``storage_tags=`` and binds the Navigator under the
# same tag - matching the citadel per-shard pattern.
# =========================================================================


def memory_navigator(
    *,
    tags: Sequence[object] = (),
) -> With:
    """Stands up a whole in-memory storage stack, gone when the process ends.

    Nothing is serialized and nothing is written: the codec is a no-op, so
    Python objects are held as themselves. That makes it the fastest backend
    and the only one where a stored value is identical, not merely equal, to
    what went in. Reach for it in tests, examples, and anywhere the state is
    meant to die with the process.

    Args:
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack. Empty binds it as the
            default that untagged Refs resolve to.

    Notes:
        - Binds the full stack: Codec, Transport, Publisher, Observer,
          Storage and Navigator, in that order, tearing down LIFO.
        - Change notification works, but only within the process.
        - Values are not copied on the way in or out, so mutating a stored
          object mutates what a later read returns.

    Example:
        app = nu.With(nu.kv.memory_navigator(), body=program)
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryStorage,
        InMemoryTransport,
        Navigator,
        noop_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, noop_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(InMemoryStorage, {}, tags=tags),
        Provide(
            Navigator,
            {"storage_type": InMemoryStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def rocksdb_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    disable_wal: bool = False,
    options: dict | None = None,
) -> With:
    """Stands up a persistent RocksDB stack with in-process change notification.

    The default choice for anything that has to survive a restart. Values are
    pickled through the binary codec, writes are transactional, and the whole
    thing needs nothing running beside it. Change notifications reach only
    listeners in this process; for cross-process, see
    ``rocksdb_navigator_redis``.

    Args:
        path: the database directory. Created if it is not there.
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack.
        read_only: open without taking the write lock, so several processes
            can read the same database at once. Writes will fail.
        secondary_path: open as a secondary instance, tailing the primary at
            ``path`` and keeping its own state under this directory. Reads
            are live-ish, writes are not possible.
        secondary_refresh_interval: the shortest gap, in seconds, between
            catch-ups with the primary. Catch-up runs lazily when a snapshot
            opens and the last one is older than this. 0 catches up on every
            snapshot; None never does, leaving freshness to the caller.
        disable_wal: skip the write-ahead log. Faster, and a crash loses
            whatever had not been flushed.
        options: raw RocksDB options, merged over the defaults.

    Notes:
        - Binds the full stack: Codec, Transport, Publisher, Observer,
          Storage and Navigator, in that order, tearing down LIFO.
        - Only one process at a time may hold the database for writing.
          Fan reads out with ``read_only`` or ``secondary_path``.
        - Values go through pickle, so anything stored has to be picklable
          and a class rename can strand old data.

    Example:
        app = nu.With(nu.kv.rocksdb_navigator(".dbcounter"), body=program)
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        Navigator,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            RocksDBStorage,
            {
                "path": path,
                "read_only": read_only,
                "secondary_path": secondary_path,
                "secondary_refresh_interval": secondary_refresh_interval,
                "disable_wal": disable_wal,
                "options": options,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": RocksDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def rocksdb_navigator_redis(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    secondary_path: str | None = None,
    secondary_refresh_interval: float | None = 0.01,
    disable_wal: bool = False,
    options: dict | None = None,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "__every__",
) -> With:
    """Stands up a persistent RocksDB stack whose changes reach other processes.

    Same storage as ``rocksdb_navigator``; what differs is who hears about a
    write. The in-process Publisher and Observer are replaced by Redis ones,
    so a change made here wakes a reactive program running somewhere else.
    That is the shape for a writer process plus a fleet of readers reacting
    to it.

    Args:
        path: the database directory. Created if it is not there.
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack.
        read_only: open without taking the write lock. Writes will fail.
        secondary_path: open as a secondary instance, tailing the primary at
            ``path`` and keeping its own state under this directory.
        secondary_refresh_interval: the shortest gap, in seconds, between
            catch-ups with the primary. Catch-up runs lazily when a snapshot
            opens and the last one is older than this. 0 catches up on every
            snapshot; None never does, leaving freshness to the caller.
        disable_wal: skip the write-ahead log. Faster, and a crash loses
            whatever had not been flushed.
        options: raw RocksDB options, merged over the defaults.
        redis_url: where the Redis carrying the notifications lives.
        channel_prefix: namespaces the pub/sub channels, so two unrelated
            deployments can share one Redis without hearing each other.

    Notes:
        - Binds Codec, Publisher, Observer, Storage and Navigator. No
          Transport: the Redis pair does not need one.
        - Redis has to be reachable when the bracket sets up, and a program
          bound to it fails at setup rather than at the first write.
        - Notifications only. The data still lives in RocksDB, so Redis
          going down costs change delivery, not storage.
        - Every writer and every listener must agree on ``channel_prefix``
          or the notifications go nowhere visible.

    Example:
        app = nu.With(
            nu.kv.rocksdb_navigator_redis(".db", redis_url="redis://cache:6379"),
            body=program,
        )
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        Navigator,
        RedisObserver,
        RedisPublisher,
        RocksDBStorage,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(
            RedisPublisher,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RocksDBStorage,
            {
                "path": path,
                "publisher_type": RedisPublisher,
                "read_only": read_only,
                "secondary_path": secondary_path,
                "secondary_refresh_interval": secondary_refresh_interval,
                "disable_wal": disable_wal,
                "options": options,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": RocksDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def text_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    log_operations: bool = False,
) -> With:
    """Stands up a JSON-on-disk stack you can open in an editor and read.

    The debugging backend. State lands in one human-readable ``state.json``,
    so the whole tree a program built can be inspected with nothing but a text
    editor, which is worth a great deal when a shape is not laying out the way
    it was meant to.

    It is a toy and says so: the entire state is held in memory and rewritten
    to disk on every commit, commits are fully serialized, there is no conflict
    detection so the last writer wins, and one process owns it at a time. Fine
    for a few hundred keys while working something out; wrong for anything
    real.

    Args:
        path: the directory holding ``state.json``, and the operation log
            when it is on.
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack.
        read_only: open without allowing writes.
        log_operations: append every put, delete, commit and abort to
            ``operations.jsonl`` beside the state, as a trace to read back.

    Notes:
        - Binds the full stack: Codec, Transport, Publisher, Observer,
          Storage and Navigator, in that order, tearing down LIFO.
        - Values go through JSON, so only JSON-able values round-trip, and
          they come back as JSON's types rather than the ones written.
        - No conflict detection means a Transaction here never raises the
          conflict that ``RetryOnConflict`` is built for. It silently
          overwrites instead.

    Example:
        app = nu.With(nu.kv.text_navigator(".dbtext"), body=program)
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        Navigator,
        TextStorage,
        text_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, text_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            TextStorage,
            {
                "path": path,
                "read_only": read_only,
                "log_operations": log_operations,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": TextStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def lmdb_navigator(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
) -> With:
    """Stands up a persistent LMDB stack with in-process change notification.

    LMDB is a memory-mapped B-tree: reads are cheap and lock-free, and many
    readers can share an environment with a writer without blocking it. What
    it asks in return is that you size the map up front, since ``map_size`` is
    a ceiling the database cannot grow past at run time.

    Args:
        path: the environment. A directory when ``subdir`` is true, the env
            file itself when it is not.
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack.
        read_only: open the environment read-only.
        map_size: the ceiling on the database, in bytes. Reserved as
            address space rather than allocated, so a generous value costs
            little. Defaults to 10 GiB.
        max_readers: how many reader slots the environment holds. A reader
            past the ceiling fails rather than waits.
        subdir: whether ``path`` names a directory or the env file.
        sync: fsync after each commit. Turning it off is faster and puts
            recent commits at risk in a crash.

    Notes:
        - Binds the full stack: Codec, Transport, Publisher, Observer,
          Storage and Navigator, in that order, tearing down LIFO.
        - Values go through pickle, so anything stored has to be picklable.
        - Exceeding ``map_size`` is a hard failure on write, not a resize.

    Example:
        app = nu.With(nu.kv.lmdb_navigator(".dblmdb"), body=program)
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        InMemoryObserver,
        InMemoryPublisher,
        InMemoryTransport,
        LMDBStorage,
        Navigator,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(InMemoryTransport, {}),
        Provide(InMemoryPublisher, {}),
        Provide(InMemoryObserver, {}),
        Provide(
            LMDBStorage,
            {
                "path": path,
                "read_only": read_only,
                "map_size": map_size,
                "max_readers": max_readers,
                "subdir": subdir,
                "sync": sync,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": LMDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


def lmdb_navigator_redis(
    path: str,
    *,
    tags: Sequence[object] = (),
    read_only: bool = False,
    map_size: int = 10 * 1024 * 1024 * 1024,
    max_readers: int = 126,
    subdir: bool = True,
    sync: bool = True,
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "nu",
) -> With:
    """Stands up a persistent LMDB stack whose changes reach other processes.

    Same storage as ``lmdb_navigator``; the in-process Publisher and Observer
    are replaced by Redis ones, so a write here wakes a reactive program in
    another process.

    Args:
        path: the environment. A directory when ``subdir`` is true, the env
            file itself when it is not.
        tags: shape tags folded onto the Storage and Navigator bindings, so
            a sharded program can name this stack.
        read_only: open the environment read-only.
        map_size: the ceiling on the database, in bytes. Defaults to 10 GiB.
        max_readers: how many reader slots the environment holds.
        subdir: whether ``path`` names a directory or the env file.
        sync: fsync after each commit.
        redis_url: where the Redis carrying the notifications lives.
        channel_prefix: namespaces the pub/sub channels, so two unrelated
            deployments can share one Redis without hearing each other.

    Notes:
        - Binds Codec, Publisher, Observer, Storage and Navigator. No
          Transport: the Redis pair does not need one.
        - Redis has to be reachable when the bracket sets up.
        - Defaults to the ``"nu"`` channel prefix, where the RocksDB Redis
          preset defaults to ``"__every__"``. Two stacks meant to hear each
          other must be given the same one explicitly.

    Example:
        app = nu.With(
            nu.kv.lmdb_navigator_redis(".dblmdb", redis_url="redis://cache:6379"),
            body=program,
        )
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import (
        Codec,
        LMDBStorage,
        Navigator,
        RedisObserver,
        RedisPublisher,
        binary_kwargs,
    )

    tags = tuple(tags)
    return With(
        Provide(Codec, binary_kwargs()),
        Provide(
            RedisPublisher,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
        Provide(
            LMDBStorage,
            {
                "path": path,
                "publisher_type": RedisPublisher,
                "read_only": read_only,
                "map_size": map_size,
                "max_readers": max_readers,
                "subdir": subdir,
                "sync": sync,
            },
            tags=tags,
        ),
        Provide(
            Navigator,
            {"storage_type": LMDBStorage, "storage_tags": tags},
            tags=tags,
        ),
    )


# =========================================================================
# Standalone Observer presets: read-only actors that consume notifications
# without owning a publishing storage.
# =========================================================================


def inmem_observer() -> With:
    """Binds the listening half of the in-process notification pair, alone.

    Transport and Observer with no Publisher and no Storage, for a program
    that reacts to changes but owns none of them. Only useful when the
    publisher it listens to lives in the same process, which is rare: two
    programs sharing a process usually share a navigator preset instead, and
    that already binds an Observer. The cross-process case is
    ``redis_observer``.

    Notes:
        - Binds nothing that can read or write data. A Ref evaluated under
          this bracket alone has no Navigator to resolve against.
        - Bind it once at process scope, not per request.

    Example:
        app = nu.With(nu.kv.inmem_observer(), body=reactor)
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import InMemoryObserver, InMemoryTransport

    return With(
        Provide(InMemoryTransport, {}),
        Provide(InMemoryObserver, {}),
    )


def redis_observer(
    redis_url: str = "redis://localhost:6379",
    channel_prefix: str = "nu",
) -> With:
    """Binds a Redis subscriber alone, for a program that only reacts.

    The listening half of a Redis-published stack, with no Publisher and no
    Storage of its own. This is what a reader process binds when the writes
    happen elsewhere: a dashboard repainting on someone else's counter, a
    handler firing on someone else's insert.

    Args:
        redis_url: where the Redis carrying the notifications lives.
        channel_prefix: must match the publishing side's, or nothing
            arrives. Note the RocksDB Redis preset defaults to
            ``"__every__"`` rather than this one's ``"nu"``.

    Notes:
        - Binds nothing that can read or write data. Pair it with a storage
          preset if the reactor also needs to read what changed.
        - Redis has to be reachable when the bracket sets up.
        - Bind it once at process scope, not per request.

    Example:
        app = nu.With(
            nu.kv.redis_observer(redis_url="redis://cache:6379"),
            body=reactor,
        )
    """
    from nu.context.fabric import Provide, With
    from nu.kv.fabrics import RedisObserver

    return With(
        Provide(
            RedisObserver,
            {"redis_url": redis_url, "channel_prefix": channel_prefix},
        ),
    )
