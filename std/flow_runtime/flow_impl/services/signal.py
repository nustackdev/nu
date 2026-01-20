"""Signal service for flow coordination."""

from __future__ import annotations

import attrs

from ._base import ServiceBase


__all__ = ["SignalService"]


@attrs.frozen
class SignalService(ServiceBase):
    """Service for signal-based coordination between flows.

    Provides signaling mechanisms for flow cancellation and coordination.
    Signals are stored in EveryShape state and can be watched reactively.

    Example:
        # Define signal path
        from pv.loc.path import PathToValue
        from everybase.views import DictView

        stop_signal: PathToValue = (("signals", DictView), ("stop", bool))

        # Touch a signal to trigger it
        runtime.signal.touch(stop_signal)

        # Wait for a signal (blocks until touched or timeout)
        runtime.signal.wait(stop_signal, timeout=5.0)

        # Clear a signal
        runtime.signal.clear(stop_signal)
    """

    pass


#     def touch(
#         self,
#         signal_path: path.PathToValue,
#         *,
#         storage_context: StorageContextType | None = None,
#     ) -> None:
#         """Touch (trigger) a signal at the given path.

#         Sets the value at the path to True, triggering any watchers.

#         Args:
#             signal_path: PathToValue to the signal location
#             storage_context: Optional storage context to use

#         Raises:
#             TypeError: If parent view does not support assignment
#         """
#         with ensure_context(self.storage, storage_context, False) as storage_context:
#             root = DictView.open_root(storage_context)
#             parent_view, address = path.navigate_value(root, signal_path)

#             if not is_assignable(parent_view):
#                 raise TypeError(
#                     f"View at {signal_path[:-1]} does not support assignment (Assignable)"
#                 )

#             parent_view[address] = True

#     # def wait(
#     #     self,
#     #     signal_path: path.PathToValue,
#     #     *,
#     #     timeout: float | None = None,
#     # ) -> bool:
#     #     """Wait for a signal to be touched.

#     #     Blocks until the signal at the given path becomes truthy or timeout expires.

#     #     Args:
#     #         signal_path: PathToValue to the signal location
#     #         timeout: Maximum seconds to wait (None = wait forever)

#     #     Returns:
#     #         True if signal was touched, False if timeout occurred

#     #     Raises:
#     #         TypeError: If parent view does not support subscript or watching
#     #     """
#     #     event = threading.Event()

#     #     def on_signal_callback(_changed_key: key.Key) -> None:
#     #         """Callback when signal changes."""
#     #         # Check if signal is now truthy
#     #         with ensure_context(self.storage, None, True) as snap:
#     #             root = DictView.open_root(snap)
#     #             parent_view, address = path.navigate_value(root, signal_path)

#     #             if not is_subscriptable(parent_view):
#     #                 return

#     #             if parent_view[address]:
#     #                 event.set()

#     #     # Set up watch on parent view
#     #     with ensure_context(self.storage, None, True) as snap:
#     #         root = DictView.open_root(snap)
#     #         parent_view, address = path.navigate_value(root, signal_path)

#     #         # Check capabilities
#     #         if not is_subscriptable(parent_view):
#     #             raise TypeError(
#     #                 f"View at {signal_path[:-1]} does not support subscript (Subscriptable)"
#     #             )

#     #         # Check if already truthy
#     #         if parent_view[address]:
#     #             return True

#     #         if not is_watchable(parent_view):
#     #             raise TypeError(f"View at {signal_path[:-1]} does not support watching (Watchable)")

#     #         # Watch for changes on parent view
#     #         subscription = parent_view.watch(self.storage, on_signal_callback, depth=0)

#     #     try:
#     #         # Wait for signal or timeout
#     #         return event.wait(timeout=timeout)
#     #     finally:
#     #         # Clean up subscription
#     #         with ensure_context(self.storage, None, True) as snap:
#     #             root = DictView.open_root(snap)
#     #             parent_view, _ = path.navigate_value(root, signal_path)
#     #             if is_watchable(parent_view):
#     #                 parent_view.unwatch(self.storage, subscription)

#     def clear(
#         self,
#         signal_path: path.PathToValue,
#         *,
#         storage_context: StorageContextType | None = None,
#     ) -> None:
#         """Clear a signal at the given path.

#         Sets the value at the path to False.

#         Args:
#             signal_path: PathToValue to the signal location
#             storage_context: Optional storage context to use

#         Raises:
#             TypeError: If parent view does not support assignment
#         """
#         with ensure_context(self.storage, storage_context, False) as storage_context:
#             root = DictView.open_root(storage_context)
#             parent_view, address = path.navigate_value(root, signal_path)

#             if not is_assignable(parent_view):
#                 raise TypeError(
#                     f"View at {signal_path[:-1]} does not support assignment (Assignable)"
#                 )

#             parent_view[address] = False

#     def is_set(
#         self,
#         signal_path: path.PathToValue,
#         *,
#         storage_context: StorageContextType | None = None,
#     ) -> bool:
#         """Check if a signal is currently set (truthy).

#         Args:
#             signal_path: PathToValue to the signal location
#             storage_context: Optional storage context to use

#         Returns:
#             True if signal is set, False otherwise

#         Raises:
#             TypeError: If parent view does not support subscript
#         """
#         with ensure_context(self.storage, storage_context, True) as storage_context:
#             root = DictView.open_root(storage_context)
#             parent_view, address = path.navigate_value(root, signal_path)

#             if not is_subscriptable(parent_view):
#                 raise TypeError(
#                     f"View at {signal_path[:-1]} does not support subscript (Subscriptable)"
#                 )

#             return bool(parent_view[address])
