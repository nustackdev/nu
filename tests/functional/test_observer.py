# """Functional tests for the subscription system."""

# import pytest

# from everyshape.adapters.in_memory import InMemoryStorage
# from everyshape.adapters.observers import InMemoryObserver
# from everyshape.storage import (
#     CompositeFilter,
#     LengthFilter,
#     PrefixFilter,
#     SubscriptionOptions,
#     SuffixFilter,
#     WildcardFilter,
# )


# @pytest.fixture
# def observer(codec):
#     """InMemoryObserver instance."""
#     obs = InMemoryObserver(codec)
#     obs.connect()
#     yield obs
#     obs.disconnect()


# @pytest.fixture
# def storage_with_observer(codec, observer):
#     """InMemoryStorage with observer."""
#     storage = InMemoryStorage(codec=codec, observer=observer)
#     storage.open()
#     yield storage
#     storage.close()


# class TestPrefixFilter:
#     def test_matches_prefix(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("users",))))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice"))
#         observer.notify(("users", "bob", "profile"))

#         assert received == [("users", "alice"), ("users", "bob", "profile")]
#         sub.close()

#     def test_no_match_different_prefix(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("users",))))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("posts", "123"))

#         assert received == []
#         sub.close()


# class TestSuffixFilter:
#     def test_matches_suffix(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=SuffixFilter(suffix=("profile",))))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice", "profile"))
#         observer.notify(("data", "profile"))

#         assert received == [("users", "alice", "profile"), ("data", "profile")]
#         sub.close()

#     def test_no_match_different_suffix(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=SuffixFilter(suffix=("profile",))))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice", "settings"))

#         assert received == []
#         sub.close()


# class TestWildcardFilter:
#     def test_matches_wildcard(self, observer):
#         received = []
#         sub = observer.subscribe(
#             SubscriptionOptions(filter=WildcardFilter(pattern=("users", "*", "profile")))
#         )
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice", "profile"))
#         observer.notify(("users", "bob", "profile"))

#         assert received == [("users", "alice", "profile"), ("users", "bob", "profile")]
#         sub.close()

#     def test_no_match_wrong_length(self, observer):
#         received = []
#         sub = observer.subscribe(
#             SubscriptionOptions(filter=WildcardFilter(pattern=("users", "*", "profile")))
#         )
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice"))
#         observer.notify(("users", "alice", "profile", "extra"))

#         assert received == []
#         sub.close()


# class TestLengthFilter:
#     def test_matches_length(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=LengthFilter(length=2)))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("a", "b"))
#         observer.notify(("x", "y"))

#         assert received == [("a", "b"), ("x", "y")]
#         sub.close()

#     def test_no_match_wrong_length(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=LengthFilter(length=2)))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("a",))
#         observer.notify(("a", "b", "c"))

#         assert received == []
#         sub.close()


# class TestCompositeFilter:
#     def test_matches_all_filters(self, observer):
#         received = []
#         sub = observer.subscribe(
#             SubscriptionOptions(
#                 filter=CompositeFilter(
#                     filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3))
#                 )
#             )
#         )
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice", "profile"))

#         assert received == [("users", "alice", "profile")]
#         sub.close()

#     def test_no_match_fails_one_filter(self, observer):
#         received = []
#         sub = observer.subscribe(
#             SubscriptionOptions(
#                 filter=CompositeFilter(
#                     filters=(PrefixFilter(prefix=("users",)), LengthFilter(length=3))
#                 )
#             )
#         )
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("users", "alice"))  # wrong length
#         observer.notify(("posts", "123", "title"))  # wrong prefix

#         assert received == []
#         sub.close()


# class TestSubscriptionBindUnbind:
#     def test_bind_multiple_receivers(self, observer):
#         received1, received2 = [], []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("data",))))

#         sub.bind(lambda k: received1.append(k))
#         sub.bind(lambda k: received2.append(k))
#         observer.notify(("data", "1"))

#         assert received1 == [("data", "1")]
#         assert received2 == [("data", "1")]
#         sub.close()

#     def test_unbind_receiver(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("data",))))

#         def callback(k):
#             received.append(k)

#         sub.bind(callback)
#         observer.notify(("data", "1"))
#         sub.unbind(callback)
#         observer.notify(("data", "2"))

#         assert received == [("data", "1")]
#         sub.close()

#     def test_context_manager(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("ctx",))))

#         with sub(lambda k: received.append(k)):
#             observer.notify(("ctx", "inside"))

#         observer.notify(("ctx", "outside"))

#         assert received == [("ctx", "inside")]
#         sub.close()


# class TestSubscriptionClose:
#     def test_close_stops_notifications(self, observer):
#         received = []
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("data",))))
#         sub.bind(lambda k: received.append(k))

#         observer.notify(("data", "before"))
#         sub.close()
#         observer.notify(("data", "after"))

#         assert received == [("data", "before")]

#     def test_close_is_idempotent(self, observer):
#         sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=("data",))))
#         sub.close()
#         sub.close()  # Should not raise


# class TestStorageIntegration:
#     def test_notifications_on_commit(self, storage_with_observer):
#         received = []
#         sub = storage_with_observer.subscribe(
#             SubscriptionOptions(filter=PrefixFilter(prefix=("store",)))
#         )
#         sub.bind(lambda k: received.append(k))

#         with storage_with_observer.transaction() as txn:
#             txn.put(("store", "key1"), "value1")
#             txn.put(("other", "key2"), "value2")

#         assert ("store", "key1") in received
#         assert ("other", "key2") not in received
#         sub.close()

#     def test_no_notifications_on_abort(self, storage_with_observer):
#         received = []
#         sub = storage_with_observer.subscribe(
#             SubscriptionOptions(filter=PrefixFilter(prefix=("store",)))
#         )
#         sub.bind(lambda k: received.append(k))

#         try:
#             with storage_with_observer.transaction() as txn:
#                 txn.put(("store", "key1"), "value1")
#                 raise ValueError("abort")
#         except ValueError:
#             pass

#         assert received == []
#         sub.close()
