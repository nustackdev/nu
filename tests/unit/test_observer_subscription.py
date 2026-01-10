"""Tests for everyshape.storage.observer.subscription module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from everyshape.storage.observer.options import PrefixFilter, SubscriptionOptions
from everyshape.storage.observer.subscription import Subscription, _SubscriptionContext


class TestSubscriptionInitialization:
    """Test cases for Subscription initialization."""

    def test_subscription_creates_with_options_and_observer(self):
        """Test that subscription initializes with options and observer."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.options is options
        assert sub._observer is mock_observer

    def test_subscription_initializes_empty_receivers(self):
        """Test that subscription starts with no receivers."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.receivers == ()
        assert len(sub._receivers) == 0

    def test_subscription_initializes_not_closed(self):
        """Test that subscription starts in open state."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.is_closed is False


class TestSubscriptionBind:
    """Test cases for Subscription.bind() method."""

    def test_bind_adds_receiver(self):
        """Test that bind() adds a receiver to the subscription."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)

        assert callback in sub.receivers
        assert len(sub.receivers) == 1

    def test_bind_multiple_receivers(self):
        """Test that bind() can add multiple receivers."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback1 = Mock()
        callback2 = Mock()
        sub.bind(callback1)
        sub.bind(callback2)

        assert callback1 in sub.receivers
        assert callback2 in sub.receivers
        assert len(sub.receivers) == 2

    def test_bind_duplicate_receiver_not_added(self):
        """Test that binding the same receiver twice doesn't add it twice."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)
        sub.bind(callback)

        assert sub.receivers.count(callback) == 1
        assert len(sub.receivers) == 1

    def test_bind_to_closed_subscription_raises_error(self):
        """Test that bind() raises ValueError if subscription is closed."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        sub.close()
        callback = Mock()

        with pytest.raises(ValueError, match="Cannot bind to a closed subscription"):
            sub.bind(callback)


class TestSubscriptionUnbind:
    """Test cases for Subscription.unbind() method."""

    def test_unbind_removes_receiver(self):
        """Test that unbind() removes a receiver from the subscription."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)
        sub.unbind(callback)

        assert callback not in sub.receivers
        assert len(sub.receivers) == 0

    def test_unbind_specific_receiver(self):
        """Test that unbind() removes only the specified receiver."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback1 = Mock()
        callback2 = Mock()
        sub.bind(callback1)
        sub.bind(callback2)
        sub.unbind(callback1)

        assert callback1 not in sub.receivers
        assert callback2 in sub.receivers
        assert len(sub.receivers) == 1

    def test_unbind_unbound_receiver_raises_error(self):
        """Test that unbind() raises ValueError if receiver is not bound."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with pytest.raises(ValueError, match="Receiver is not bound to this subscription"):
            sub.unbind(callback)

    def test_unbind_preserves_error_chain(self):
        """Test that unbind() preserves the original ValueError in the chain."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with pytest.raises(ValueError) as exc_info:
            sub.unbind(callback)

        assert exc_info.value.__cause__ is not None


class TestSubscriptionBindContext:
    """Test cases for Subscription.bind_context() method."""

    def test_bind_context_returns_context_manager(self):
        """Test that bind_context() returns a _SubscriptionContext."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = sub.bind_context(callback)

        assert isinstance(context, _SubscriptionContext)

    def test_bind_context_binds_on_enter(self):
        """Test that context manager binds receiver on __enter__."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with sub.bind_context(callback):
            assert callback in sub.receivers

    def test_bind_context_unbinds_on_exit(self):
        """Test that context manager unbinds receiver on __exit__."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with sub.bind_context(callback):
            pass

        assert callback not in sub.receivers

    def test_bind_context_returns_subscription(self):
        """Test that context manager __enter__ returns the subscription."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with sub.bind_context(callback) as result:
            assert result is sub

    def test_bind_context_unbinds_even_on_exception(self):
        """Test that context manager unbinds receiver even if exception occurs."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        try:
            with sub.bind_context(callback):
                raise RuntimeError("Test error")
        except RuntimeError:
            pass

        assert callback not in sub.receivers

    def test_bind_context_ignores_unbind_error_on_exit(self):
        """Test that context manager ignores errors when unbinding on exit."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with sub.bind_context(callback):
            # Manually unbind before context exit
            sub.unbind(callback)

        # No exception should be raised


class TestSubscriptionCall:
    """Test cases for Subscription.__call__() method."""

    def test_call_returns_context_manager(self):
        """Test that __call__() returns a _SubscriptionContext."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = sub(callback)

        assert isinstance(context, _SubscriptionContext)

    def test_call_works_as_shorthand(self):
        """Test that __call__() works as shorthand for bind_context."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()

        with sub(callback):
            assert callback in sub.receivers

        assert callback not in sub.receivers


class TestSubscriptionClose:
    """Test cases for Subscription.close() method."""

    def test_close_marks_subscription_closed(self):
        """Test that close() marks the subscription as closed."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.is_closed is False
        sub.close()
        assert sub.is_closed is True

    def test_close_clears_receivers(self):
        """Test that close() clears all receivers."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback1 = Mock()
        callback2 = Mock()
        sub.bind(callback1)
        sub.bind(callback2)

        sub.close()

        assert len(sub.receivers) == 0

    def test_close_calls_observer_close_subscription(self):
        """Test that close() notifies the observer."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        sub.close()

        mock_observer._close_subscription.assert_called_once_with(sub)

    def test_close_idempotent(self):
        """Test that close() is idempotent."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        sub.close()
        sub.close()

        mock_observer._close_subscription.assert_called_once_with(sub)

    def test_close_prevents_binding(self):
        """Test that bind() fails after close()."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        sub.close()
        callback = Mock()

        with pytest.raises(ValueError):
            sub.bind(callback)


class TestSubscriptionNotify:
    """Test cases for Subscription.notify() method."""

    def test_notify_calls_all_receivers(self):
        """Test that notify() calls all bound receivers."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback1 = Mock()
        callback2 = Mock()
        sub.bind(callback1)
        sub.bind(callback2)

        key = ("users", "alice")
        list(sub.notify(key))

        callback1.assert_called_once_with(key)
        callback2.assert_called_once_with(key)

    def test_notify_with_no_receivers(self):
        """Test that notify() with no receivers doesn't raise error."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        key = ("users", "alice")
        # notify() is a generator, consume it
        list(sub.notify(key))

    def test_notify_yields_exceptions(self):
        """Test that notify() yields exceptions from receivers."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        error1 = ValueError("error 1")
        error2 = RuntimeError("error 2")

        def callback1(_key):
            raise error1

        def callback2(_key):
            raise error2

        sub.bind(callback1)
        sub.bind(callback2)

        key = ("users", "alice")
        exceptions = list(sub.notify(key))

        assert len(exceptions) == 2
        assert error1 in exceptions
        assert error2 in exceptions

    def test_notify_continues_after_exception(self):
        """Test that notify() continues calling receivers even if one fails."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback1 = Mock(side_effect=ValueError("error 1"))
        callback2 = Mock()
        callback3 = Mock(side_effect=RuntimeError("error 3"))

        sub.bind(callback1)
        sub.bind(callback2)
        sub.bind(callback3)

        key = ("users", "alice")
        list(sub.notify(key))

        callback1.assert_called_once_with(key)
        callback2.assert_called_once_with(key)
        callback3.assert_called_once_with(key)

    def test_notify_is_generator(self):
        """Test that notify() returns a generator."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)

        key = ("users", "alice")
        result = sub.notify(key)

        # Check it's a generator
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_notify_lazy_evaluation(self):
        """Test that notify() evaluates lazily."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)

        key = ("users", "alice")
        result = sub.notify(key)

        # Callback should not be called yet
        callback.assert_not_called()

        # Consume the generator
        list(result)

        # Now it should be called
        callback.assert_called_once_with(key)


class TestSubscriptionProperties:
    """Test cases for Subscription properties."""

    def test_options_property_returns_options(self):
        """Test that options property returns subscription options."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.options is options

    def test_filter_property_returns_filter(self):
        """Test that filter property returns the filter from options."""
        mock_observer = Mock()
        filter_obj = PrefixFilter(prefix=("users",))
        options = SubscriptionOptions(filter=filter_obj)
        sub = Subscription(_options=options, _observer=mock_observer)

        assert sub.filter is filter_obj

    def test_receivers_property_returns_tuple(self):
        """Test that receivers property returns a tuple."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        assert isinstance(sub.receivers, tuple)

    def test_receivers_property_is_immutable(self):
        """Test that receivers property returns immutable tuple."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)

        receivers = sub.receivers

        # Verify it's a tuple
        assert isinstance(receivers, tuple)

        # Attempting to modify should fail
        with pytest.raises((TypeError, AttributeError)):
            receivers[0] = Mock()

    def test_receivers_property_returns_copy(self):
        """Test that receivers property returns a new tuple each time."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        sub.bind(callback)

        receivers1 = sub.receivers
        receivers2 = sub.receivers

        assert receivers1 == receivers2
        assert receivers1 is not receivers2


class TestSubscriptionHash:
    """Test cases for Subscription.__hash__() method."""

    def test_subscription_is_hashable(self):
        """Test that subscription can be hashed."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        hash_value = hash(sub)
        assert isinstance(hash_value, int)

    def test_subscription_hash_based_on_identity(self):
        """Test that subscription hash is based on object identity."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        sub1 = Subscription(_options=options, _observer=mock_observer)
        sub2 = Subscription(_options=options, _observer=mock_observer)

        assert hash(sub1) != hash(sub2)

    def test_subscription_can_be_added_to_set(self):
        """Test that subscription can be added to a set."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))

        sub1 = Subscription(_options=options, _observer=mock_observer)
        sub2 = Subscription(_options=options, _observer=mock_observer)

        subscription_set = {sub1, sub2}
        assert len(subscription_set) == 2


class TestSubscriptionContextManager:
    """Test cases for _SubscriptionContext helper class."""

    def test_subscription_context_binds_on_enter(self):
        """Test that _SubscriptionContext binds receiver on __enter__."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = _SubscriptionContext(sub, callback)

        context.__enter__()

        assert callback in sub.receivers

    def test_subscription_context_returns_subscription_on_enter(self):
        """Test that _SubscriptionContext.__enter__ returns subscription."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = _SubscriptionContext(sub, callback)

        result = context.__enter__()

        assert result is sub

    def test_subscription_context_unbinds_on_exit(self):
        """Test that _SubscriptionContext unbinds receiver on __exit__."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = _SubscriptionContext(sub, callback)

        context.__enter__()
        context.__exit__(None, None, None)

        assert callback not in sub.receivers

    def test_subscription_context_handles_unbind_error(self):
        """Test that _SubscriptionContext handles unbind errors gracefully."""
        mock_observer = Mock()
        options = SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        sub = Subscription(_options=options, _observer=mock_observer)

        callback = Mock()
        context = _SubscriptionContext(sub, callback)

        context.__enter__()
        # Manually remove before exit
        sub.unbind(callback)

        # Should not raise
        context.__exit__(None, None, None)
