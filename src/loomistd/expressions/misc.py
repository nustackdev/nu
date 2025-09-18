from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import List, Optional, Type

from loomi.expression import Context, Expression, ExpressionError, ExpressionPath, ExpressionValue
from loomi.tree import Path
from loomistd.app import SyncApp

from .logger import logger


class Throttle(Expression[SyncApp]):
    """
    Throttle expression execution to a maximum frequency.

    This expression ensures the wrapped expression executes at most once
    per interval, regardless of how often it's triggered. Subsequent calls
    within the interval are ignored.

    Use cases:
    - Rate limiting API calls
    - Reducing screen update frequency
    - Preventing excessive state writes

    Args:
        expression: Child expression to throttle
        interval_ms: Minimum milliseconds between executions (can be value or state path)

    Examples:
        ```python
        # Throttle screen updates to max 60fps (~16.67ms)
        Throttle(
            RenderBuffer(app, Path().buffer),
            interval_ms=16
        )

        # Throttle API calls with configurable interval
        Throttle(
            SendHeartbeat(app),
            interval_ms=Path().config.heartbeat_interval
        )

        # Throttle function calls
        Throttle(
            Function(app, app.process_batch),
            interval_ms=100
        )
        ```
    """

    def __init__(self, app, expression: Expression, interval_ms: ExpressionValue, **kwargs):
        super().__init__(app, **kwargs)
        self.expression = expression
        self.interval_ms = interval_ms

        # Thread-safe tracking of last execution time
        # Use instance-specific key for global state
        self._last_execution_key = f"_throttle_{id(self)}_last_execution"
        self._lock = threading.RLock()

    def do_evaluate(self, context: "Context") -> None:
        """Execute child expression only if interval has passed."""

        # Resolve interval from state if needed
        with self.app.state.tree.snapshot() as snapshot:
            interval_ms = self._resolve_value(
                self.interval_ms, self.app.state.tree, snapshot, context
            )

        if not isinstance(interval_ms, (int, float)):
            raise ExpressionError(
                f"Throttle interval must be a number (got {type(interval_ms).__name__})",
                expression=self,
            )

        if interval_ms < 0:
            raise ExpressionError(
                f"Throttle interval must be non-negative (got {interval_ms})", expression=self
            )

        interval_seconds = interval_ms / 1000.0
        current_time = time.perf_counter()

        with self._lock:
            # Get last execution time from global state
            last_execution = getattr(self.app, self._last_execution_key, 0.0)

            # Check if enough time has passed
            time_since_last = current_time - last_execution

            if time_since_last >= interval_seconds:
                # Execute the child expression
                logger.debug(
                    f"Throttle allowing execution (time since last: {time_since_last:.3f}s)",
                    extra={
                        "interval_seconds": interval_seconds,
                        "time_since_last": time_since_last,
                        "expression_type": type(self.expression).__name__,
                    },
                )

                # Update last execution time
                setattr(self.app, self._last_execution_key, current_time)

                # Execute child with proper context
                child_context = self._create_child_context(
                    context, child_expression=self.expression
                )
                self.expression.evaluate(child_context)

            else:
                # Throttled - skip execution
                remaining_time = interval_seconds - time_since_last
                logger.debug(
                    f"Throttle blocking execution (remaining: {remaining_time:.3f}s)",
                    extra={
                        "interval_seconds": interval_seconds,
                        "time_since_last": time_since_last,
                        "remaining_time": remaining_time,
                    },
                )


class OnListChange(Expression[SyncApp]):
    name: str

    def __init__(
        self,
        app,
        name: str,
        path: ExpressionPath,
        expression: Expression,
        stop_when: ExpressionValue | None = None,
        depth: int = 1,
        **kwargs,
    ):
        super().__init__(app, name=name, **kwargs)
        self.path = path
        self.expression = expression
        self.depth = depth
        self.stop_when = stop_when

    def do_evaluate(self, context: "Context") -> None:
        """Block and wait for queue changes, executing expression sequentially."""
        # Event to signal when a change occurs
        change_event = threading.Event()
        change_path = tuple()

        # Create callback function that signals change events
        def on_change_callback(changed_path_tuple):
            """Signal that a change occurred."""
            nonlocal change_path
            change_path = changed_path_tuple
            change_event.set()

        # Convert path to tuple format for backend subscription
        with self.app.state.tree.snapshot() as snapshot:
            view, path = self._resolve_path(self.path, self.app.state.tree, snapshot, context)
            watch_path = view.path.join(path)

        try:
            to_unsub = False
            # Blocking loop: wait for changes and process them sequentially
            while True:
                # Subscribe to changes at the watch path
                subscription = self.app.state.tree.at(*watch_path.components).subscribe(
                    callback=on_change_callback, depth=self.depth
                )
                to_unsub = True

                # Block until a change occurs
                change_event.wait()

                # Clear the event for the next iteration
                change_event.clear()

                # Clean up subscription
                try:
                    self.app.state.tree.unsubscribe(subscription)
                    to_unsub = False
                except Exception as cleanup_error:
                    print(f"Error cleaning up WatchChange subscription: {cleanup_error}")

                print(f"Change detected at {change_path}")

                # get item
                item = None
                with self.app.state.tree.snapshot() as snapshot:
                    item = self._resolve_value(
                        Path(change_path[1:]), self.app.state.tree, snapshot, context
                    )

                # Execute the provided expression
                try:
                    self.expression.evaluate(
                        self._create_child_context(
                            context,
                            child_expression=self.expression,
                            child_attributes={
                                self.name: {
                                    "path": change_path,
                                    "index": int(change_path[-1]),
                                    "item": item,
                                },
                            },
                        )
                    )
                except Exception as expression_error:
                    raise expression_error

                # After expression completes, loop back to wait for next change
                # (change_event.wait() will block until the next change occurs)

                # Check stop condition after expression completes
                if self.stop_when is not None:
                    with self.app.state.tree.snapshot() as snapshot:
                        stop_value = self._resolve_value(
                            self.stop_when, self.app.state.tree, snapshot, context
                        )
                        if stop_value:  # Break if condition is truthy
                            break
        finally:
            # Clean up subscription
            try:
                if to_unsub:
                    self.app.state.tree.unsubscribe(subscription)
            except Exception as cleanup_error:
                print(f"Error cleaning up WatchChange subscription: {cleanup_error}")


class RepeatOnFailure(Expression[SyncApp]):
    """
    Repeats an inner expression on failure until success or max attempts reached.

    This expression executes the inner expression and if it fails (raises an exception),
    it will retry the execution up to max_attempts times, with an optional delay between attempts.

    Args:
        app: The sync application instance
        expression: The inner expression to execute and potentially retry
        max_attempts: Maximum number of attempts (default: 3)
        delay: Delay in seconds between retry attempts (default: 0)
        retry_exceptions: Tuple of exception types to retry on. If None, retries on any exception.
        exponential_backoff: If True, delays increase exponentially (delay * attempt_number)
        **kwargs: Additional keyword arguments passed to parent Expression

    Example:
        ```python
        # Retry a PumpFun buy operation up to 5 times with 2 second delays
        RepeatOnFailure(
            self,
            PumpFunBuy(
                self,
                transaction_body=self.get_tx_body(),
                result_path=Path().buy_tx,
                ca_pubkey="token_address_here",
                sol_amount=0.005,
            ),
            max_attempts=5,
            delay=2.0,
            exponential_backoff=True,
        )

        # Retry only on specific exceptions
        RepeatOnFailure(
            self,
            TransactionSend(
                self,
                Path().buy_tx,
                Path().network.info.recent_blockhash,
                "rpc",
            ),
            max_attempts=3,
            delay=1.0,
            retry_exceptions=(ConnectionError, TimeoutError),
        )
        ```

    Internal Behavior:
        - Attempts to execute the inner expression
        - On success: completes normally
        - On failure: waits for delay period, then retries
        - After max_attempts failures: raises the last encountered exception
        - Respects cancellation between attempts
    """

    def __init__(
        self,
        app: SyncApp,
        expression: Expression,
        max_attempts: int = 3,
        delay: float = 0.0,
        retry_exceptions: Optional[tuple[Type[Exception], ...]] = None,
        exponential_backoff: bool = False,
        **kwargs,
    ):
        super().__init__(app, **kwargs)

        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if delay < 0:
            raise ValueError("delay must be non-negative")

        self.expression = expression
        self.max_attempts = max_attempts
        self.delay = delay
        self.retry_exceptions = retry_exceptions
        self.exponential_backoff = exponential_backoff

    def do_evaluate(self, context: "Context") -> None:
        """Execute the inner expression with retry logic on failure."""

        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                # Execute the inner expression
                self.expression.evaluate(
                    self._create_child_context(
                        context,
                        child_expression=self.expression,
                        child_attributes={
                            "retry_attempt": attempt,
                            "max_attempts": self.max_attempts,
                            "is_retry": attempt > 1,
                        },
                    )
                )

                # If we get here, the expression succeeded
                if attempt > 1:
                    print(f"✓ Expression succeeded on attempt {attempt}")
                return

            except Exception as e:
                last_exception = e

                # Check if this exception type should trigger a retry
                if self.retry_exceptions is not None:
                    if not isinstance(e, self.retry_exceptions):
                        # This exception type should not be retried, re-raise immediately
                        raise e

                # Check if we've exhausted all attempts
                if attempt >= self.max_attempts:
                    print(f"✗ Expression failed after {self.max_attempts} attempts")
                    break

                # Log the failure and prepare for retry
                print(f"✗ Attempt {attempt} failed: {str(e)}")
                print(f"⟳ Retrying in {self._get_delay_for_attempt(attempt)} seconds...")

                # Apply delay before retry (if configured)
                if self.delay > 0:
                    # Check for cancellation before delaying
                    if self.is_cancelled(context):
                        raise ExpressionError(
                            "RepeatOnFailure cancelled during retry delay",
                            expression=self,
                            cause=e,
                        )

                    delay_duration = self._get_delay_for_attempt(attempt)
                    time.sleep(delay_duration)

                    # Check for cancellation after delay
                    if self.is_cancelled(context):
                        return

        # If we get here, all attempts failed
        error_msg = f"Expression failed after {self.max_attempts} attempts"
        if last_exception:
            error_msg += f". Last error: {str(last_exception)}"

        raise ExpressionError(
            error_msg,
            expression=self,
            cause=last_exception,
        )

    def _get_delay_for_attempt(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        if self.exponential_backoff:
            return self.delay * attempt
        else:
            return self.delay


class ConditionalWaiter(Expression[SyncApp]):
    """
    Conditional expression that waits for state changes when condition is false.

    Workflow:
    1. Evaluate condition
    2. If True -> execute inner expressions, then loop back to step 1
    3. If False -> wait for state changes on watched paths, then loop back to step 1
    """

    def __init__(
        self,
        app,
        condition: ExpressionValue,
        expression: Expression,
        watch_paths: Optional[List[ExpressionPath]] = None,
        depth: int = 1,
        name: str = "conditional_waiter",
        **kwargs,
    ):
        """
        Initialize conditional waiter.

        Args:
            app: Application instance
            condition: Condition to evaluate (ExpressionValue)
            expression: Expression to run when condition is True
            watch_paths: List of paths to watch for changes (optional)
            depth: Subscription depth for state changes
            name: Name for this expression instance
            **kwargs: Additional expression kwargs
        """
        super().__init__(app, name=name, **kwargs)
        self.condition = condition
        self.expression = expression
        self.watch_paths = watch_paths or []
        self.depth = depth

    def do_evaluate(self, context: "Context") -> None:
        """Main evaluation loop with condition checking and state waiting."""
        print(f"🔄 Starting ConditionalWaiter: {self.name}")

        # Main loop
        while not self.is_cancelled(context):
            try:
                # Step 1: Evaluate condition
                with self.app.state.tree.snapshot() as snapshot:
                    condition_result = self._resolve_value(
                        self.condition, self.app.state.tree, snapshot, context
                    )

                print(f"🔍 Condition check: {bool(condition_result)}")

                if condition_result:
                    # Step 2: Condition is True - execute inner expressions
                    print("✅ Condition True - executing inner expression")

                    try:
                        self.expression.evaluate(
                            self._create_child_context(
                                context,
                                child_expression=self.expression,
                            )
                        )
                        print("✅ Inner expression completed successfully")
                    except Exception as expression_error:
                        print("❌ Error in inner expression: {expression_error}")
                        # Re-raise to let parent handle it
                        raise expression_error

                    # After successful execution, loop back to check condition again
                    continue

                else:
                    # Step 3: Condition is False - wait for state changes
                    print("⏳ Condition False - waiting for state changes...")
                    self._wait_for_state_changes(context)

            except Exception as e:
                if not self.is_cancelled(context):
                    print(f"❌ Error in ConditionalWaiter: {e}")
                    raise ExpressionError(
                        f"Failed in conditional waiter '{self.name}': {e}",
                        expression=self,
                        cause=e,
                    )
                break

        print(f"🛑 ConditionalWaiter stopped: {self.name}")

    def _wait_for_state_changes(self, context: "Context") -> None:
        """Wait for changes on watched paths using state tree subscriptions."""
        if not self.watch_paths:
            print("⚠️  No watch paths specified - cannot wait for changes")
            # Without watch paths, we can't wait for specific changes
            # Fall back to a short sleep to prevent busy loop
            import time

            time.sleep(0.1)
            return

        # Event to signal when changes occur
        change_event = threading.Event()
        subscriptions = []

        def on_change_callback(changed_path_tuple):
            """Signal that a change occurred."""
            print(f"🔔 State change detected at: {changed_path_tuple}")
            change_event.set()

        try:
            # Subscribe to all watch paths
            with self.app.state.tree.snapshot() as snapshot:
                for watch_path in self.watch_paths:
                    try:
                        view, path = self._resolve_path(
                            watch_path, self.app.state.tree, snapshot, context
                        )
                        full_path = view.path.join(path)

                        subscription = self.app.state.tree.at(*full_path.components).subscribe(
                            callback=on_change_callback, depth=self.depth
                        )
                        subscriptions.append(subscription)
                        print(f"👁️  Watching path: {full_path}")

                    except Exception as path_error:
                        print(f"⚠️  Could not watch path {watch_path}: {path_error}")

            if not subscriptions:
                print("⚠️  No valid subscriptions created")
                return

            # Block until a change occurs or we're cancelled
            while not change_event.is_set() and not self.is_cancelled(context):
                change_event.wait(timeout=0.1)  # Short timeout to check cancellation

            if change_event.is_set():
                print("✨ Change detected - rechecking condition...")

        finally:
            # Clean up subscriptions
            for subscription in subscriptions:
                try:
                    self.app.state.tree.unsubscribe(subscription)
                except Exception as cleanup_error:
                    print(f"⚠️  Error cleaning up subscription: {cleanup_error}")


class ConditionalWaiterSimple(Expression[SyncApp]):
    """
    Simplified version that auto-detects paths from the condition.
    Uses a more basic approach - polls the condition periodically.
    """

    def __init__(
        self,
        app,
        condition: ExpressionValue,
        expression: Expression,
        poll_interval: float = 0.1,
        one_shot: bool = True,
        count: int | None = None,
        **kwargs,
    ):
        """
        Initialize simple conditional waiter with polling.

        Args:
            app: Application instance
            condition: Condition to evaluate
            expression: Expression to run when condition is True
            poll_interval: How often to check condition when False (seconds)
            one_shot: Whether to stop after the first successful execution
        """
        super().__init__(app, **kwargs)
        self.condition = condition
        self.expression = expression
        self.poll_interval = poll_interval
        self.one_shot = one_shot
        self.count = count

    def do_evaluate(self, context: "Context") -> None:
        """Simple polling-based conditional evaluation."""
        import time

        print(f"🔄 Starting Simple ConditionalWaiter: {self.name}")
        print(f"📊 Poll interval: {self.poll_interval}s")

        successful_iterations = 0
        while not self.is_cancelled(context):
            try:
                # Evaluate condition
                with self.app.state.tree.snapshot() as snapshot:
                    condition_result = self._resolve_value(
                        self.condition, self.app.state.tree, snapshot, context
                    )

                if condition_result:
                    print("✅ Condition True - executing inner expression")

                    successful_iterations += 1

                    self.expression.evaluate(
                        self._create_child_context(
                            context,
                            child_expression=self.expression,
                        )
                    )
                    print("✅ Inner expression completed")

                    if self.one_shot or (
                        self.count is not None and self.count >= successful_iterations
                    ):
                        # Stop after the first successful execution
                        break
                else:
                    print(f"⏳ Condition False - waiting {self.poll_interval}s...")
                    time.sleep(self.poll_interval)

            except Exception as e:
                if not self.is_cancelled(context):
                    print(f"❌ Error in Simple ConditionalWaiter: {e}")
                    raise

        print(f"🛑 Simple ConditionalWaiter stopped: {self.name}")


class ConditionalWaiterWithElif(Expression[SyncApp]):
    """
    Enhanced conditional waiter that supports if/elif/else functionality.
    Evaluates conditions in order and executes the first matching expression.
    """

    def __init__(
        self,
        app,
        conditions_and_expressions: List[tuple[ExpressionValue, Expression]],
        else_expression: Optional[Expression] = None,
        poll_interval: float = 0.1,
        one_shot: bool = True,
        count: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize conditional waiter with elif support.

        Args:
            app: Application instance
            conditions_and_expressions: List of (condition, expression) pairs
            else_expression: Optional expression to run when no conditions are True
            poll_interval: How often to check conditions when all are False (seconds)
            one_shot: Whether to stop after the first successful execution
            count: Maximum number of successful executions before stopping
        """
        super().__init__(app, **kwargs)

        if not conditions_and_expressions:
            raise ValueError("At least one condition-expression pair must be provided")

        self.conditions_and_expressions = conditions_and_expressions
        self.else_expression = else_expression
        self.poll_interval = poll_interval
        self.one_shot = one_shot
        self.count = count

    def do_evaluate(self, context: "Context") -> None:
        """Polling-based conditional evaluation with elif support."""

        print(
            f"🔄 Starting ConditionalWaiter with {len(self.conditions_and_expressions)} conditions: {self.name}"
        )
        print(f"📊 Poll interval: {self.poll_interval}s")
        if self.else_expression:
            print("📋 Else expression provided")

        successful_iterations = 0

        while not self.is_cancelled(context):
            try:
                executed_expression = False

                # Check conditions in order (if/elif pattern)
                for i, (condition, expression) in enumerate(self.conditions_and_expressions):
                    with self.app.state.tree.snapshot() as snapshot:
                        condition_result = self._resolve_value(
                            condition, self.app.state.tree, snapshot, context
                        )

                    if condition_result:
                        condition_name = f"condition_{i + 1}" if i > 0 else "if_condition"
                        print(f"✅ {condition_name} True - executing corresponding expression")

                        successful_iterations += 1
                        executed_expression = True

                        expression.evaluate(
                            self._create_child_context(
                                context,
                                child_expression=expression,
                            )
                        )
                        print(f"✅ Expression for {condition_name} completed")
                        break  # Exit the condition checking loop

                # Handle else case if no conditions were True
                if not executed_expression and self.else_expression:
                    print("🔄 No conditions True - executing else expression")
                    successful_iterations += 1
                    executed_expression = True

                    self.else_expression.evaluate(
                        self._create_child_context(
                            context,
                            child_expression=self.else_expression,
                        )
                    )
                    print("✅ Else expression completed")

                # Check stopping conditions
                if executed_expression:
                    if self.one_shot or (
                        self.count is not None and successful_iterations >= self.count
                    ):
                        break
                else:
                    # All conditions were False and no else expression
                    print(f"⏳ All conditions False - waiting {self.poll_interval}s...")
                    time.sleep(self.poll_interval)

            except Exception as e:
                if not self.is_cancelled(context):
                    print(f"❌ Error in ConditionalWaiter: {e}")
                    raise

        print(f"🛑 ConditionalWaiter stopped: {self.name} (executed {successful_iterations} times)")


class ParallelMap(Expression[SyncApp]):
    """
    Execute an expression in parallel for each item in a list.

    This expression takes a list (from state path or direct value) and runs
    a child expression for each item in the list concurrently, with configurable
    maximum concurrency.

    The child expression can access the current item and its index via:
    - Path().var(name, "item") - the current list item
    - Path().var(name, "index") - the current item's index in the list

    Args:
        list_value: ExpressionValue that resolves to a list to iterate over
        expression: Expression to execute for each list item
        max_concurrency: Maximum number of concurrent executions
            - 1 means sequential execution
            - >1 means limit to N concurrent executions
            - -1 or 0 means unlimited concurrency (default: -1)
        name: Variable name for accessing item data in child expression (default: "mapper")

    Examples:
        ```python
        # Process list of tokens in parallel
        Map(
            self,
            list_value=Path().tokens_to_process,
            expression=ProcessToken(self, Path().var("mapper", "item")),
            max_concurrency=5,
            name="mapper"
        )

        # Process with index access
        Map(
            self,
            list_value=["token1", "token2", "token3"],
            expression=Sequence(
                self,
                Print(self, f"Processing item {Path().var('processor', 'index')}"),
                ProcessToken(self, Path().var("processor", "item"))
            ),
            name="processor"
        )

        # Sequential processing (max_concurrency=1)
        Map(
            self,
            list_value=Path().critical_operations,
            expression=CriticalOperation(self, Path().var("sequential", "item")),
            max_concurrency=1,
            name="sequential"
        )
        ```
    """

    name: str

    def __init__(
        self,
        app,
        list_value: ExpressionValue,
        expression: Expression,
        max_concurrency: int = -1,
        name: str = "mapper",
        **kwargs,
    ):
        """
        Initialize the Map expression.

        Args:
            list_value: ExpressionValue that resolves to a list
            expression: Expression to execute for each list item
            max_concurrency: Maximum number of concurrent executions
            name: Variable name for accessing item data in child expression
        """
        super().__init__(app, name=name, **kwargs)

        # Validate max_concurrency
        if max_concurrency < -1:
            error_msg = f"Invalid max_concurrency: {max_concurrency}. Must be >= -1"
            logger.error(
                "Invalid max_concurrency for Map expression",
                extra={
                    "max_concurrency": max_concurrency,
                    "valid_range": ">= -1",
                },
            )
            raise ValueError(error_msg)

        self.list_value = list_value
        self.expression = expression
        self._max_concurrency = max_concurrency

    def do_evaluate(self, context: "Context") -> None:
        """
        Evaluate the child expression for each item in the list in parallel.

        Args:
            context: The execution context
        """
        try:
            # Resolve the list value
            with self.app.state.tree.snapshot() as snapshot:
                resolved_list = self._resolve_value(
                    self.list_value, self.app.state.tree, snapshot, context
                )

            # Validate that we got a list
            if not isinstance(resolved_list, (list, tuple)):
                error_msg = f"List value must resolve to a list or tuple, got {type(resolved_list).__name__}"
                logger.error(
                    "Map expression list_value did not resolve to a list",
                    extra={
                        "resolved_type": type(resolved_list).__name__,
                        "resolved_value": str(resolved_list)[:100],  # Truncate for logging
                    },
                )
                raise ExpressionError(error_msg, expression=self)

            list_length = len(resolved_list)

            if list_length == 0:
                logger.info("Map expression: empty list, nothing to process")
                return

            # Calculate effective max workers
            max_workers = self._max_concurrency if self._max_concurrency > 0 else list_length

            logger.info(
                "Starting Map expression evaluation",
                extra={
                    "list_length": list_length,
                    "max_concurrency": self._max_concurrency,
                    "effective_max_workers": max_workers,
                    "expression_type": type(self.expression).__name__,
                    "variable_name": self.name,
                },
            )

            # Execute in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all items for parallel processing
                futures = []
                for index, item in enumerate(resolved_list):
                    logger.debug(
                        "Submitting item for parallel processing",
                        extra={
                            "item_index": index,
                            "item_value": str(item)[:50],  # Truncate for logging
                            "expression_type": type(self.expression).__name__,
                            "map_id": id(self),
                        },
                    )

                    # Create child context with item and index accessible
                    child_context = self._create_child_context(
                        context,
                        child_expression=self.expression,
                        child_index=index,
                        child_attributes={
                            self.name: {
                                "item": item,
                                "index": index,
                            },
                        },
                    )

                    future = executor.submit(self.expression.evaluate, child_context)
                    futures.append((index, future))

                logger.debug(
                    "All items submitted for processing, waiting for completion",
                    extra={
                        "futures_count": len(futures),
                        "max_workers": max_workers,
                    },
                )

                # Wait for all futures to complete
                _, _ = wait([future for _, future in futures])

                # Check for exceptions in completed futures
                exceptions = []
                completed_count = 0

                for index, future in futures:
                    try:
                        future.result()  # This will raise if the future had an exception
                        completed_count += 1
                        logger.debug(
                            "Item processing completed successfully",
                            extra={
                                "item_index": index,
                                "completed_count": completed_count,
                                "total_count": list_length,
                            },
                        )
                    except Exception as e:
                        logger.error(
                            "Item processing failed in Map expression",
                            extra={
                                "item_index": index,
                                "expression_type": type(self.expression).__name__,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "completed_count": completed_count,
                                "total_count": list_length,
                            },
                            exc_info=True,
                        )
                        exceptions.append((index, e))

                # If any exceptions occurred, raise the first one
                if exceptions:
                    first_exception_index, first_exception = exceptions[0]
                    logger.error(
                        "Map expression failed due to item processing errors",
                        extra={
                            "failed_count": len(exceptions),
                            "successful_count": completed_count,
                            "total_count": list_length,
                            "first_failure_index": first_exception_index,
                            "map_id": id(self),
                        },
                    )
                    raise first_exception

                logger.info(
                    "Map expression completed successfully",
                    extra={
                        "processed_count": completed_count,
                        "list_length": list_length,
                        "max_workers": max_workers,
                        "expression_id": id(self),
                    },
                )

        except Exception as e:
            logger.error(
                "Map expression execution failed",
                extra={
                    "list_length": list_length if "list_length" in locals() else "unknown",
                    "max_workers": max_workers if "max_workers" in locals() else "unknown",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "expression_id": id(self),
                },
                exc_info=True,
            )
            raise
