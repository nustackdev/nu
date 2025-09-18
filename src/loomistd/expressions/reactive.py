"""
Reactive expressions for the Loomi framework.

This module provides reactive expressions that respond to state changes in the state tree,
enabling event-driven programming patterns with proper resource management and thread safety.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from loomi.expression import Context, Expression, ExpressionError, ExpressionPath, ExpressionValue
from loomistd.app import SyncApp

from .logger import logger


@dataclass
class ChangeSource:
    """Configuration for watching a specific path."""

    path: ExpressionPath
    depth: int = 1
    filter_fn: Optional[Callable[[Any], bool]] = None
    name: Optional[str] = None


@dataclass
class ReactionStep:
    """Stage definition for chained reactive expressions."""

    input_path: ExpressionPath
    expression: Expression
    output_path: Optional[ExpressionPath] = None


class WatchForChange(Expression[SyncApp]):
    """
    Watch a path for changes and execute expression after each change.

    This expression subscribes to changes at the specified path, and when a change
    occurs, it unsubscribes, executes the provided expression, then re-subscribes
    for the next change. This creates a cycle: watch → change → unsubscribe → execute → re-subscribe.

    Args:
        path: State path to watch for changes
        expression: Expression to execute when change occurs
        depth: Subscription depth for change detection (default: 1)
        stop_when: Optional condition to stop watching (default: None)

    Examples:
        ```python
        # React to user status changes
        WatchForChange(
            app,
            path=Path().user.status,
            expression=Print(app, "User status changed!")
        )

        # Watch with stop condition
        WatchForChange(
            app,
            path=Path().tasks.queue,
            expression=ProcessNextTask(app),
            stop_when=Path().shutdown_requested
        )
        ```
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        *,
        depth: int = 1,
        stop_when: ExpressionValue = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.expression = expression
        self.depth = depth
        self.stop_when = stop_when

    def do_evaluate(self, context: "Context") -> None:
        """Watch for changes and execute expression after each change."""
        logger.info(f"Starting WatchForChange on path: {self.path}")

        while not self.is_cancelled(context):
            try:
                # Set up change detection
                change_event = threading.Event()

                def on_change_callback(changed_path_tuple):
                    logger.debug(f"Change detected at: {changed_path_tuple}")
                    change_event.set()

                # Subscribe to changes
                with self.app.state.tree.snapshot() as snapshot:
                    view, resolved_path = self._resolve_path(
                        self.path, self.app.state.tree, snapshot, context
                    )
                    full_path = view.path.join(resolved_path)

                subscription = self.app.state.tree.at(*full_path.components).subscribe(
                    callback=on_change_callback, depth=self.depth
                )

                try:
                    # Wait for change
                    logger.debug("Waiting for change...")
                    while not change_event.is_set() and not self.is_cancelled(context):
                        change_event.wait(timeout=0.1)

                    if self.is_cancelled(context):
                        return

                    logger.debug("Change detected, executing expression")

                finally:
                    # Always unsubscribe before executing
                    try:
                        self.app.state.tree.unsubscribe(subscription)
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Error cleaning up WatchForChange subscription: {cleanup_error}"
                        )

                # Execute the expression
                try:
                    child_context = self._create_child_context(
                        context, child_expression=self.expression
                    )
                    self.expression.evaluate(child_context)
                    logger.debug("Expression execution completed")
                except Exception as expression_error:
                    logger.error(f"Error executing expression: {expression_error}")
                    raise

                # Check stop condition
                if self.stop_when is not None:
                    with self.app.state.tree.snapshot() as snapshot:
                        stop_value = self._resolve_value(
                            self.stop_when, self.app.state.tree, snapshot, context
                        )
                        if stop_value:
                            logger.info("Stop condition met, ending watch")
                            break

            except Exception as e:
                logger.error(f"Error in WatchForChange: {e}")
                raise ExpressionError(f"WatchForChange failed: {e}", expression=self, cause=e)

        logger.info("WatchForChange completed")


class WatchAsync(Expression[SyncApp]):
    """
    Continuously watch for changes and execute expressions in background threads.

    Unlike WatchForChange, this expression maintains its subscription and processes
    changes asynchronously without blocking. Changes can be accumulated and processed
    in batches or individually with configurable concurrency.

    Args:
        path: State path to watch for changes
        expression: Expression to execute for each change
        max_concurrent: Maximum number of concurrent executions (default: 3)
        accumulate: Whether to accumulate changes for batch processing (default: False)
        batch_size: Number of changes to batch together when accumulating (default: 1)

    Examples:
        ```python
        # Process changes asynchronously
        WatchAsync(
            app,
            path=Path().events.stream,
            expression=ProcessEvent(app, Path().var("event", "data")),
            max_concurrent=5
        )

        # Batch changes for efficient processing
        WatchAsync(
            app,
            path=Path().logs.entries,
            expression=ProcessLogBatch(app, Path().var("batch", "items")),
            accumulate=True,
            batch_size=10
        )
        ```
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        *,
        max_concurrent: int = 3,
        accumulate: bool = False,
        batch_size: int = 1,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.expression = expression
        self.max_concurrent = max_concurrent
        self.accumulate = accumulate
        self.batch_size = batch_size
        self._change_queue = deque()
        self._queue_lock = threading.RLock()

    def do_evaluate(self, context: "Context") -> None:
        """Start async watching and change processing."""
        logger.info(f"Starting WatchAsync on path: {self.path}")

        change_queue = deque()
        queue_lock = threading.RLock()

        def on_change_callback(changed_path_tuple):
            with queue_lock:
                # Get the actual changed data
                try:
                    with self.app.state.tree.snapshot() as snapshot:
                        change_data = self._resolve_value(
                            changed_path_tuple, self.app.state.tree, snapshot, context
                        )
                    change_queue.append(
                        {"path": changed_path_tuple, "data": change_data, "timestamp": time.time()}
                    )
                    logger.debug(f"Queued change from: {changed_path_tuple}")
                except Exception as e:
                    logger.warning(f"Failed to resolve change data: {e}")

        # Subscribe once and keep subscription active
        with self.app.state.tree.snapshot() as snapshot:
            view, resolved_path = self._resolve_path(
                self.path, self.app.state.tree, snapshot, context
            )
            full_path = view.path.join(resolved_path)

        subscription = self.app.state.tree.at(*full_path.components).subscribe(
            callback=on_change_callback, depth=1
        )

        try:
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:

                def process_changes():
                    """Process accumulated changes."""
                    while not self.is_cancelled(context):
                        changes_to_process = []

                        # Collect changes for processing
                        with queue_lock:
                            if not change_queue:
                                time.sleep(0.01)  # Short sleep when no changes
                                continue

                            if self.accumulate:
                                # Take up to batch_size changes
                                for _ in range(min(self.batch_size, len(change_queue))):
                                    if change_queue:
                                        changes_to_process.append(change_queue.popleft())
                            else:
                                # Take single change
                                if change_queue:
                                    changes_to_process.append(change_queue.popleft())

                        # Process collected changes
                        if changes_to_process:
                            try:
                                child_context = self._create_child_context(
                                    context,
                                    child_expression=self.expression,
                                    child_attributes={
                                        "changes" if self.accumulate else "event": {
                                            "items": (
                                                changes_to_process
                                                if self.accumulate
                                                else changes_to_process[0]
                                            ),
                                            "count": len(changes_to_process),
                                        }
                                    },
                                )
                                self.expression.evaluate(child_context)
                                logger.debug(f"Processed {len(changes_to_process)} changes")
                            except Exception as e:
                                logger.error(f"Error processing changes: {e}")

                # Start processing in background
                future = executor.submit(process_changes)

                # Wait for completion or cancellation
                while not self.is_cancelled(context) and not future.done():
                    time.sleep(0.1)

                logger.info("WatchAsync processing completed")

        finally:
            # Clean up subscription
            try:
                self.app.state.tree.unsubscribe(subscription)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up WatchAsync subscription: {cleanup_error}")


class WatchAny(Expression[SyncApp]):
    """
    Watch multiple paths and execute expression when any of them changes.

    Args:
        sources: List of ChangeSource configurations to watch
        expression: Expression to execute when any source changes
        first_wins: If True, stop after first change (default: False)

    Examples:
        ```python
        # React to changes on any user field
        WatchAny(
            app,
            sources=[
                ChangeSource(Path().user.name),
                ChangeSource(Path().user.email),
                ChangeSource(Path().user.avatar)
            ],
            expression=RefreshUserDisplay(app)
        )

        # Stop after first match
        WatchAny(
            app,
            sources=[
                ChangeSource(Path().signals.stop),
                ChangeSource(Path().signals.pause)
            ],
            expression=HandleSignal(app),
            first_wins=True
        )
        ```
    """

    def __init__(
        self,
        app,
        sources: List[ChangeSource],
        expression: Expression,
        *,
        first_wins: bool = False,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.sources = sources
        self.expression = expression
        self.first_wins = first_wins

    def do_evaluate(self, context: "Context") -> None:
        """Watch multiple sources and react to any change."""
        logger.info(f"Starting WatchAny on {len(self.sources)} sources")

        change_event = threading.Event()
        change_info = {"source": None, "path": None}
        subscriptions = []

        def create_callback(source_name, source_path):
            def callback(changed_path_tuple):
                change_info["source"] = source_name
                change_info["path"] = changed_path_tuple
                change_event.set()

            return callback

        try:
            # Subscribe to all sources
            with self.app.state.tree.snapshot() as snapshot:
                for i, source in enumerate(self.sources):
                    source_name = source.name or f"source_{i}"

                    view, resolved_path = self._resolve_path(
                        source.path, self.app.state.tree, snapshot, context
                    )
                    full_path = view.path.join(resolved_path)

                    callback = create_callback(source_name, source.path)
                    subscription = self.app.state.tree.at(*full_path.components).subscribe(
                        callback=callback, depth=source.depth
                    )
                    subscriptions.append(subscription)
                    logger.debug(f"Subscribed to {source_name} at {full_path}")

            # Watch for changes
            while not self.is_cancelled(context):
                change_event.wait(timeout=0.1)

                if change_event.is_set():
                    logger.debug(f"Change detected from {change_info['source']}")

                    # Execute expression with change info
                    child_context = self._create_child_context(
                        context,
                        child_expression=self.expression,
                        child_attributes={
                            "change": {"source": change_info["source"], "path": change_info["path"]}
                        },
                    )
                    self.expression.evaluate(child_context)

                    if self.first_wins:
                        logger.info("First match found, stopping WatchAny")
                        break

                    # Reset for next change
                    change_event.clear()
                    change_info["source"] = None
                    change_info["path"] = None

        finally:
            # Clean up all subscriptions
            for subscription in subscriptions:
                try:
                    self.app.state.tree.unsubscribe(subscription)
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up WatchAny subscription: {cleanup_error}")

        logger.info("WatchAny completed")


class Throttle(Expression[SyncApp]):
    """
    Throttle expression execution to a maximum frequency.

    Enhanced version with leading and trailing edge control. Leading edge means
    execute immediately on first call, trailing edge means execute after the
    interval if there were additional calls.

    Args:
        expression: Child expression to throttle
        interval_ms: Minimum milliseconds between executions
        leading: Execute on leading edge of interval (default: True)
        trailing: Execute on trailing edge if pending (default: False)

    Examples:
        ```python
        # Throttle to max 10 fps, execute immediately
        Throttle(
            app,
            expression=UpdateDisplay(app),
            interval_ms=100,
            leading=True
        )

        # Throttle with trailing execution
        Throttle(
            app,
            expression=SaveToDatabase(app),
            interval_ms=1000,
            leading=True,
            trailing=True
        )
        ```
    """

    def __init__(
        self,
        app,
        expression: Expression,
        interval_ms: ExpressionValue,
        *,
        leading: bool = True,
        trailing: bool = False,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.expression = expression
        self.interval_ms = interval_ms
        self.leading = leading
        self.trailing = trailing

        # Thread-safe state
        self._last_execution_key = f"_throttle_{id(self)}_last_execution"
        self._pending_key = f"_throttle_{id(self)}_pending"
        self._lock = threading.RLock()

    def do_evaluate(self, context: "Context") -> None:
        """Execute child expression with throttling."""
        # Resolve interval
        with self.app.state.tree.snapshot() as snapshot:
            interval_ms = self._resolve_value(
                self.interval_ms, self.app.state.tree, snapshot, context
            )

        if not isinstance(interval_ms, (int, float)) or interval_ms < 0:
            raise ExpressionError(
                f"Throttle interval must be non-negative number (got {interval_ms})",
                expression=self,
            )

        interval_seconds = interval_ms / 1000.0
        current_time = time.perf_counter()

        with self._lock:
            last_execution = getattr(self.app, self._last_execution_key, 0.0)
            pending = getattr(self.app, self._pending_key, False)
            time_since_last = current_time - last_execution

            if time_since_last >= interval_seconds:
                # Interval has passed - can execute
                if self.leading:
                    logger.debug("Throttle executing (leading edge)")
                    setattr(self.app, self._last_execution_key, current_time)
                    setattr(self.app, self._pending_key, False)

                    child_context = self._create_child_context(
                        context, child_expression=self.expression
                    )
                    self.expression.evaluate(child_context)
                else:
                    # Not leading edge, mark as pending
                    setattr(self.app, self._pending_key, True)
            else:
                # Still within interval
                setattr(self.app, self._pending_key, True)

                if self.trailing:
                    # Schedule trailing execution
                    remaining_time = interval_seconds - time_since_last

                    def trailing_execution():
                        time.sleep(remaining_time)
                        with self._lock:
                            if getattr(self.app, self._pending_key, False):
                                logger.debug("Throttle executing (trailing edge)")
                                setattr(self.app, self._last_execution_key, time.perf_counter())
                                setattr(self.app, self._pending_key, False)

                                child_context = self._create_child_context(
                                    context, child_expression=self.expression
                                )
                                self.expression.evaluate(child_context)

                    threading.Thread(target=trailing_execution, daemon=True).start()
                else:
                    logger.debug(
                        f"Throttle blocked (remaining: {interval_seconds - time_since_last:.3f}s)"
                    )


class Debounce(Expression[SyncApp]):
    """
    Execute expression only after changes stop for specified duration.

    Resets the timer on each execution. Useful for things like search-as-you-type
    where you only want to execute after the user stops typing.

    Args:
        expression: Expression to execute after quiet period
        delay_ms: Milliseconds to wait after last execution
        max_wait_ms: Maximum wait time before forcing execution (optional)

    Examples:
        ```python
        # Search after user stops typing
        Debounce(
            app,
            expression=PerformSearch(app, Path().search.query),
            delay_ms=300
        )

        # Auto-save with maximum wait time
        Debounce(
            app,
            expression=AutoSave(app),
            delay_ms=1000,
            max_wait_ms=5000
        )
        ```
    """

    def __init__(
        self,
        app,
        expression: Expression,
        delay_ms: ExpressionValue,
        *,
        max_wait_ms: ExpressionValue = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.expression = expression
        self.delay_ms = delay_ms
        self.max_wait_ms = max_wait_ms

        # State tracking
        self._timer_key = f"_debounce_{id(self)}_timer"
        self._first_call_key = f"_debounce_{id(self)}_first_call"
        self._lock = threading.RLock()

    def do_evaluate(self, context: "Context") -> None:
        """Execute expression after delay period of no additional calls."""
        with self.app.state.tree.snapshot() as snapshot:
            delay_ms = self._resolve_value(self.delay_ms, self.app.state.tree, snapshot, context)
            max_wait_ms = None
            if self.max_wait_ms is not None:
                max_wait_ms = self._resolve_value(
                    self.max_wait_ms, self.app.state.tree, snapshot, context
                )

        if not isinstance(delay_ms, (int, float)) or delay_ms < 0:
            raise ExpressionError(
                f"Debounce delay must be non-negative number (got {delay_ms})", expression=self
            )

        delay_seconds = delay_ms / 1000.0
        max_wait_seconds = max_wait_ms / 1000.0 if max_wait_ms else None
        current_time = time.perf_counter()

        with self._lock:
            # Cancel existing timer
            existing_timer = getattr(self.app, self._timer_key, None)
            if existing_timer:
                existing_timer.cancel()

            # Track first call for max wait
            first_call_time = getattr(self.app, self._first_call_key, current_time)
            if existing_timer is None:  # First call in sequence
                setattr(self.app, self._first_call_key, current_time)
                first_call_time = current_time

            def execute_debounced():
                with self._lock:
                    logger.debug("Debounce executing after delay")
                    setattr(self.app, self._timer_key, None)
                    setattr(self.app, self._first_call_key, 0.0)

                    child_context = self._create_child_context(
                        context, child_expression=self.expression
                    )
                    self.expression.evaluate(child_context)

            # Check if max wait time exceeded
            if max_wait_seconds and (current_time - first_call_time) >= max_wait_seconds:
                logger.debug("Debounce executing (max wait exceeded)")
                execute_debounced()
            else:
                # Start new timer
                timer = threading.Timer(delay_seconds, execute_debounced)
                setattr(self.app, self._timer_key, timer)
                timer.start()
                logger.debug(f"Debounce timer reset ({delay_seconds:.3f}s)")


class RateLimit(Expression[SyncApp]):
    """
    Enforce maximum number of executions per time window.

    Tracks execution history and either drops excess executions or queues them
    for later processing when the rate limit allows.

    Args:
        expression: Expression to rate limit
        max_executions: Maximum executions per window
        window_ms: Time window in milliseconds
        queue_size: Queue size for excess executions (0 = drop, -1 = unlimited)

    Examples:
        ```python
        # Limit API calls to 10 per second
        RateLimit(
            app,
            expression=CallAPI(app, Path().request),
            max_executions=10,
            window_ms=1000
        )

        # Queue excess executions
        RateLimit(
            app,
            expression=ProcessItem(app),
            max_executions=5,
            window_ms=1000,
            queue_size=20
        )
        ```
    """

    def __init__(
        self,
        app,
        expression: Expression,
        max_executions: int,
        window_ms: int,
        *,
        queue_size: int = 0,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.expression = expression
        self.max_executions = max_executions
        self.window_ms = window_ms
        self.queue_size = queue_size

        # State tracking
        self._history_key = f"_ratelimit_{id(self)}_history"
        self._queue_key = f"_ratelimit_{id(self)}_queue"
        self._lock = threading.RLock()

    def do_evaluate(self, context: "Context") -> None:
        """Execute expression within rate limits."""
        if self.max_executions <= 0:
            raise ExpressionError("Rate limit max_executions must be positive", expression=self)

        window_seconds = self.window_ms / 1000.0
        current_time = time.perf_counter()

        with self._lock:
            # Get execution history
            history = getattr(self.app, self._history_key, deque())
            if not isinstance(history, deque):
                history = deque()
                setattr(self.app, self._history_key, history)

            # Clean old entries
            cutoff_time = current_time - window_seconds
            while history and history[0] <= cutoff_time:
                history.popleft()

            if len(history) < self.max_executions:
                # Within rate limit - execute immediately
                history.append(current_time)
                logger.debug(f"RateLimit executing ({len(history)}/{self.max_executions})")

                child_context = self._create_child_context(
                    context, child_expression=self.expression
                )
                self.expression.evaluate(child_context)

            else:
                # Rate limit exceeded
                if self.queue_size == 0:
                    # Drop execution
                    logger.debug("RateLimit dropping execution (queue disabled)")
                    return

                # Queue for later
                execution_queue = getattr(self.app, self._queue_key, deque())
                if not isinstance(execution_queue, deque):
                    execution_queue = deque()
                    setattr(self.app, self._queue_key, execution_queue)

                if self.queue_size > 0 and len(execution_queue) >= self.queue_size:
                    logger.debug("RateLimit dropping execution (queue full)")
                    return

                # Add to queue
                execution_queue.append((context, current_time))
                logger.debug(f"RateLimit queued execution ({len(execution_queue)} queued)")

                # Process queue in background
                def process_queue():
                    while execution_queue:
                        with self._lock:
                            # Check if we can execute now
                            now = time.perf_counter()
                            history = getattr(self.app, self._history_key, deque())

                            # Clean history
                            cutoff = now - window_seconds
                            while history and history[0] <= cutoff:
                                history.popleft()

                            if len(history) < self.max_executions:
                                # Can execute
                                queued_context, queued_time = execution_queue.popleft()
                                history.append(now)

                                logger.debug("RateLimit executing queued item")
                                child_context = self._create_child_context(
                                    queued_context, child_expression=self.expression
                                )
                                self.expression.evaluate(child_context)
                            else:
                                # Still rate limited
                                time.sleep(0.1)

                threading.Thread(target=process_queue, daemon=True).start()


class WatchUntil(Expression[SyncApp]):
    """
    Watch paths until a condition becomes true, then execute expression.

    Monitors specified paths for changes and evaluates the condition after each
    change. When the condition becomes true, executes the expression.

    Args:
        condition: Condition to evaluate (becomes expression trigger)
        expression: Expression to execute when condition is true
        watch_paths: Paths to monitor for changes that might affect condition
        re_arm: Whether to continue watching after condition is met (default: True)

    Examples:
        ```python
        # Wait for system to be ready
        WatchUntil(
            app,
            condition=Path().system.ready,
            expression=StartServices(app),
            watch_paths=[Path().system.status, Path().system.health]
        )

        # Wait for specific value
        WatchUntil(
            app,
            condition=lambda: get_user_count() > 100,
            expression=SendAlert(app, "User milestone reached!"),
            watch_paths=[Path().users.count],
            re_arm=False
        )
        ```
    """

    def __init__(
        self,
        app,
        condition: ExpressionValue,
        expression: Expression,
        watch_paths: List[ExpressionPath],
        *,
        re_arm: bool = True,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.condition = condition
        self.expression = expression
        self.watch_paths = watch_paths
        self.re_arm = re_arm

    def do_evaluate(self, context: "Context") -> None:
        """Watch paths and execute when condition becomes true."""
        logger.info(f"Starting WatchUntil with {len(self.watch_paths)} paths")

        while not self.is_cancelled(context):
            change_event = threading.Event()
            subscriptions = []

            def on_change_callback(changed_path_tuple):
                logger.debug(f"WatchUntil change detected: {changed_path_tuple}")
                change_event.set()

            try:
                # Subscribe to all watch paths
                with self.app.state.tree.snapshot() as snapshot:
                    for watch_path in self.watch_paths:
                        view, resolved_path = self._resolve_path(
                            watch_path, self.app.state.tree, snapshot, context
                        )
                        full_path = view.path.join(resolved_path)

                        subscription = self.app.state.tree.at(*full_path.components).subscribe(
                            callback=on_change_callback, depth=1
                        )
                        subscriptions.append(subscription)

                # Initial condition check
                with self.app.state.tree.snapshot() as snapshot:
                    condition_result = self._resolve_value(
                        self.condition, self.app.state.tree, snapshot, context
                    )

                if condition_result:
                    logger.debug("WatchUntil condition already true, executing")
                    child_context = self._create_child_context(
                        context, child_expression=self.expression
                    )
                    self.expression.evaluate(child_context)

                    if not self.re_arm:
                        logger.info("WatchUntil not re-arming, stopping")
                        break
                else:
                    # Wait for changes and check condition
                    while not self.is_cancelled(context):
                        change_event.wait(timeout=0.1)

                        if change_event.is_set():
                            # Check condition after change
                            with self.app.state.tree.snapshot() as snapshot:
                                condition_result = self._resolve_value(
                                    self.condition, self.app.state.tree, snapshot, context
                                )

                            if condition_result:
                                logger.debug("WatchUntil condition became true, executing")
                                child_context = self._create_child_context(
                                    context, child_expression=self.expression
                                )
                                self.expression.evaluate(child_context)

                                if not self.re_arm:
                                    logger.info("WatchUntil not re-arming, stopping")
                                    return
                                else:
                                    break  # Re-arm by breaking to outer loop

                            change_event.clear()

            finally:
                # Clean up subscriptions
                for subscription in subscriptions:
                    try:
                        self.app.state.tree.unsubscribe(subscription)
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Error cleaning up WatchUntil subscription: {cleanup_error}"
                        )

        logger.info("WatchUntil completed")


class OnTransition(Expression[SyncApp]):
    """
    Execute expression when watched value transitions between specific states.

    Monitors a path and triggers when the value changes from one specific value
    to another, or any transition if from_value/to_value are not specified.

    Args:
        path: Path to monitor for value transitions
        expression: Expression to execute on matching transition
        from_value: Source value for transition (None = any value)
        to_value: Target value for transition (None = any value)

    Examples:
        ```python
        # Connection state transitions
        OnTransition(
            app,
            path=Path().connection.status,
            from_value="disconnected",
            to_value="connected",
            expression=ShowConnectionAlert(app)
        )

        # Any value change
        OnTransition(
            app,
            path=Path().user.preferences,
            expression=SavePreferences(app)
        )
        ```
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        *,
        from_value: Any = None,
        to_value: Any = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.expression = expression
        self.from_value = from_value
        self.to_value = to_value
        self._previous_value_key = f"_transition_{id(self)}_previous"

    def do_evaluate(self, context: "Context") -> None:
        """Watch for value transitions and execute on match."""
        logger.info(f"Starting OnTransition for path: {self.path}")

        # Get initial value
        with self.app.state.tree.snapshot() as snapshot:
            current_value = self._resolve_value(self.path, self.app.state.tree, snapshot, context)
        setattr(self.app, self._previous_value_key, current_value)

        change_event = threading.Event()

        def on_change_callback(changed_path_tuple):
            change_event.set()

        # Subscribe to path changes
        with self.app.state.tree.snapshot() as snapshot:
            view, resolved_path = self._resolve_path(
                self.path, self.app.state.tree, snapshot, context
            )
            full_path = view.path.join(resolved_path)

        subscription = self.app.state.tree.at(*full_path.components).subscribe(
            callback=on_change_callback, depth=0  # Exact path only
        )

        try:
            while not self.is_cancelled(context):
                change_event.wait(timeout=0.1)

                if change_event.is_set():
                    # Get new value and compare
                    with self.app.state.tree.snapshot() as snapshot:
                        new_value = self._resolve_value(
                            self.path, self.app.state.tree, snapshot, context
                        )

                    previous_value = getattr(self.app, self._previous_value_key)

                    # Check if transition matches criteria
                    transition_matches = True
                    if self.from_value is not None and previous_value != self.from_value:
                        transition_matches = False
                    if self.to_value is not None and new_value != self.to_value:
                        transition_matches = False

                    if transition_matches and new_value != previous_value:
                        logger.debug(f"OnTransition matched: {previous_value} → {new_value}")

                        child_context = self._create_child_context(
                            context,
                            child_expression=self.expression,
                            child_attributes={
                                "transition": {
                                    "from": previous_value,
                                    "to": new_value,
                                    "path": self.path,
                                }
                            },
                        )
                        self.expression.evaluate(child_context)

                    # Update previous value
                    setattr(self.app, self._previous_value_key, new_value)
                    change_event.clear()

        finally:
            try:
                self.app.state.tree.unsubscribe(subscription)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up OnTransition subscription: {cleanup_error}")

        logger.info("OnTransition completed")


class BatchChanges(Expression[SyncApp]):
    """
    Accumulate changes and execute expression when batch is full or timeout occurs.

    Collects changes from the watched path and executes the expression either when
    the batch reaches the specified size or when the timeout expires.

    Args:
        path: Path to watch for changes
        expression: Expression to execute with batched changes
        batch_size: Number of changes to collect before executing
        timeout_ms: Maximum time to wait before processing partial batch
        flush_on: Optional condition to force immediate batch processing

    Examples:
        ```python
        # Batch log entries
        BatchChanges(
            app,
            path=Path().logs.entries,
            expression=ProcessLogBatch(app, Path().var("batch", "items")),
            batch_size=100,
            timeout_ms=5000
        )

        # Batch with flush condition
        BatchChanges(
            app,
            path=Path().events.stream,
            expression=ProcessEventBatch(app, Path().var("batch", "items")),
            batch_size=50,
            timeout_ms=10000,
            flush_on=Path().force_flush
        )
        ```
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        expression: Expression,
        batch_size: int,
        timeout_ms: int,
        *,
        flush_on: ExpressionValue = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.expression = expression
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
        self.flush_on = flush_on

    def do_evaluate(self, context: "Context") -> None:
        """Accumulate changes and batch process them."""
        logger.info(
            f"Starting BatchChanges (batch_size={self.batch_size}, timeout={self.timeout_ms}ms)"
        )

        batch = []
        batch_lock = threading.RLock()
        last_batch_time = time.time()
        timeout_seconds = self.timeout_ms / 1000.0

        change_event = threading.Event()

        def on_change_callback(changed_path_tuple):
            nonlocal last_batch_time

            try:
                # Get the changed data
                with self.app.state.tree.snapshot() as snapshot:
                    change_data = self._resolve_value(
                        changed_path_tuple, self.app.state.tree, snapshot, context
                    )

                with batch_lock:
                    batch.append(
                        {"path": changed_path_tuple, "data": change_data, "timestamp": time.time()}
                    )

                    if len(batch) == 1:  # First item in new batch
                        last_batch_time = time.time()

                    logger.debug(f"BatchChanges: {len(batch)}/{self.batch_size} items")
                    change_event.set()

            except Exception as e:
                logger.warning(f"Error processing change for batch: {e}")

        # Subscribe to path
        with self.app.state.tree.snapshot() as snapshot:
            view, resolved_path = self._resolve_path(
                self.path, self.app.state.tree, snapshot, context
            )
            full_path = view.path.join(resolved_path)

        subscription = self.app.state.tree.at(*full_path.components).subscribe(
            callback=on_change_callback, depth=1
        )

        try:
            while not self.is_cancelled(context):
                change_event.wait(timeout=0.1)

                should_process = False
                current_batch = []

                with batch_lock:
                    if batch:
                        # Check batch size
                        if len(batch) >= self.batch_size:
                            should_process = True
                            logger.debug("BatchChanges: batch size reached")

                        # Check timeout
                        elif time.time() - last_batch_time >= timeout_seconds:
                            should_process = True
                            logger.debug("BatchChanges: timeout reached")

                        # Check flush condition
                        if self.flush_on is not None:
                            try:
                                with self.app.state.tree.snapshot() as snapshot:
                                    flush_value = self._resolve_value(
                                        self.flush_on, self.app.state.tree, snapshot, context
                                    )
                                if flush_value:
                                    should_process = True
                                    logger.debug("BatchChanges: flush condition met")
                            except Exception as e:
                                logger.warning(f"Error checking flush condition: {e}")

                        if should_process:
                            current_batch = list(batch)
                            batch.clear()
                            last_batch_time = time.time()

                if should_process and current_batch:
                    logger.info(f"BatchChanges processing {len(current_batch)} items")

                    child_context = self._create_child_context(
                        context,
                        child_expression=self.expression,
                        child_attributes={
                            "batch": {
                                "items": current_batch,
                                "count": len(current_batch),
                                "first_timestamp": current_batch[0]["timestamp"],
                                "last_timestamp": current_batch[-1]["timestamp"],
                            }
                        },
                    )
                    self.expression.evaluate(child_context)

                change_event.clear()

        finally:
            # Process any remaining items
            with batch_lock:
                if batch:
                    logger.info(f"BatchChanges processing final {len(batch)} items")
                    child_context = self._create_child_context(
                        context,
                        child_expression=self.expression,
                        child_attributes={
                            "batch": {"items": list(batch), "count": len(batch), "final": True}
                        },
                    )
                    self.expression.evaluate(child_context)

            try:
                self.app.state.tree.unsubscribe(subscription)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up BatchChanges subscription: {cleanup_error}")

        logger.info("BatchChanges completed")


class SwitchOnChange(Expression[SyncApp]):
    """
    Route to different expressions based on what changed or change characteristics.

    Watches for changes and routes them to different expressions based on the
    change path, data, or custom routing logic.

    Args:
        path: Base path to watch for changes
        cases: Dictionary mapping route keys to expressions
        route_fn: Function to determine route key from change data
        default_expression: Expression to use if no route matches

    Examples:
        ```python
        def route_by_path(change_data):
            path = change_data.get("path", ())
            if "users" in path:
                return "user_change"
            elif "orders" in path:
                return "order_change"
            return "default"

        SwitchOnChange(
            app,
            path=Path().data,
            route_fn=route_by_path,
            cases={
                "user_change": UpdateUserDisplay(app),
                "order_change": ProcessOrder(app),
            },
            default_expression=LogChange(app)
        )
        ```
    """

    def __init__(
        self,
        app,
        path: ExpressionPath,
        route_fn: Callable[[Dict[str, Any]], str],
        cases: Dict[str, Expression],
        *,
        default_expression: Expression = None,
        **kwargs,
    ):
        super().__init__(app, **kwargs)
        self.path = path
        self.route_fn = route_fn
        self.cases = cases
        self.default_expression = default_expression

    def do_evaluate(self, context: "Context") -> None:
        """Watch for changes and route to appropriate expressions."""
        logger.info(f"Starting SwitchOnChange with {len(self.cases)} cases")

        change_event = threading.Event()
        change_data = {}

        def on_change_callback(changed_path_tuple):
            try:
                with self.app.state.tree.snapshot() as snapshot:
                    data = self._resolve_value(
                        changed_path_tuple, self.app.state.tree, snapshot, context
                    )

                change_data.update(
                    {"path": changed_path_tuple, "data": data, "timestamp": time.time()}
                )
                change_event.set()

            except Exception as e:
                logger.warning(f"Error processing change for switch: {e}")

        # Subscribe to path
        with self.app.state.tree.snapshot() as snapshot:
            view, resolved_path = self._resolve_path(
                self.path, self.app.state.tree, snapshot, context
            )
            full_path = view.path.join(resolved_path)

        subscription = self.app.state.tree.at(*full_path.components).subscribe(
            callback=on_change_callback, depth=1
        )

        try:
            while not self.is_cancelled(context):
                change_event.wait(timeout=0.1)

                if change_event.is_set():
                    try:
                        # Determine route
                        route_key = self.route_fn(change_data)
                        logger.debug(f"SwitchOnChange routing to: {route_key}")

                        # Get expression for route
                        expression = self.cases.get(route_key, self.default_expression)

                        if expression:
                            child_context = self._create_child_context(
                                context,
                                child_expression=expression,
                                child_attributes={"change": change_data, "route": route_key},
                            )
                            expression.evaluate(child_context)
                        else:
                            logger.debug(f"No expression found for route: {route_key}")

                    except Exception as e:
                        logger.error(f"Error in SwitchOnChange routing: {e}")

                    change_event.clear()
                    change_data.clear()

        finally:
            try:
                self.app.state.tree.unsubscribe(subscription)
            except Exception as cleanup_error:
                logger.warning(f"Error cleaning up SwitchOnChange subscription: {cleanup_error}")

        logger.info("SwitchOnChange completed")
