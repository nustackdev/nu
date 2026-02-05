# Flow

A Flow controls execution order. It answers: **when** things run.

## Core Idea

Flows order children. They return nothing — they're transparent wrappers that control sequencing, branching, parallelism, and repetition.

```python
import every_flow as f

tree = f.Seq(
    User.name.set("Alice"),
    User.age.set(30),
    f.Print("done", User.name.get()),
)
await tree.execute(ctx)
```

Flows can contain Terms, other Flows, or Spans. Terms cannot contain Flows — computation doesn't impose order of execution.

## Built-in Flows

All flows live in the `every_flow` package.

### Control

```python
# Sequential execution
f.Seq(step_a, step_b, step_c)

# Conditional
f.If(counter.get() > 0, handle_positive, handle_negative)

# While loop
f.While(queue.length() > 0, process_next)

# Do-while (body runs at least once)
f.DoWhile(should_continue, body)

# Infinite loop (until external cancellation)
f.Forever(poll_and_process)

# Multi-way branch
f.Switch(mode.get(), cases={"fast": fast, "slow": slow}, default=fallback)
```

### Parallel

```python
# Run all concurrently (asyncio.gather)
f.Parallel(fetch_users, fetch_posts, fetch_comments)

# First to finish wins, cancel the rest
f.Race(fetch_primary, fetch_replica)

# All must succeed, cancel on first failure
f.All(validate_input, check_permissions, load_config)

# First success wins, tolerate failures
f.Any(try_cache, try_db, try_remote)
```

### Iteration

```python
# Counted loop
i_ref = SomeShape.counter  # IntRef
f.ForRange(0, 10, body, index=i_ref)

# Iterate over collection
f.ForEach(items.get(), process_item)

# Concurrent iteration with concurrency limit
f.ForEachParallel(urls.get(), fetch_url, max_parallel=5)
```

### Error Handling

```python
# Try/catch/finally
err_ref = SomeShape.error  # StrRef
f.TryCatch(risky_op, catch=error_handler, finally_=cleanup, error=err_ref)

# Retry with exponential backoff
attempt_ref = SomeShape.attempt  # IntRef
f.Retry(flaky_op, max_attempts=5, delay=1.0, backoff=2.0, attempt=attempt_ref)

# Assert (raises AssertionError on failure)
f.Assert(balance.get() > 0, message="insufficient balance")
```

### Timing

```python
# Delay
f.Delay(1.5)                             # just sleep
f.Delay(1.0, then_do_this)               # sleep then execute

# Timeout
f.Timeout(30, slow_operation)             # raises TimeoutError
f.Timeout(5, slow_op, on_timeout=fallback) # runs fallback instead

# Rate limiting
f.Throttle(1.0, check_update)            # at most once per second
f.Debounce(0.5, process_search)          # wait for quiet period
```

### Reactive

```python
# React once to a change
f.React(user.name.on_change(), handle_name_change)

# React to every change, forever
f.ReactForever(queue.on_children_change(), sync_task)

# React while condition holds
f.ReactWhile(
    sensor.temperature.on_change(),
    sensor.temperature.get() < 100.0,
    f.If(sensor.temperature.get() > 80.0, send_warning),
)
```

### I/O

```python
f.Print("status", counter.get())         # [Print:status] 42
f.Log("disk full", level="error")        # structured logging
f.Debug(x, y, labels=["x", "y"])         # [DEBUG] x=42 y='hello'
```

### Assertion Helpers

```python
f.AssertExists(user.name)                # raises if missing
f.AssertEmpty(queue)                      # raises if not empty
f.AssertEquals(status, "active")          # raises if not equal
f.SkipIfMissing(config.api_key, call_api) # skip if no API key
f.SkipIfEmpty(results, process_results)   # skip if empty
```

## Example: Producer-Consumer with Reactive Monitoring

```python
import every_flow as f
from every_pv import IntRef, FloatRef
from every_dict import IntRef as MemIntRef
from everyshape import Shape

class Sensor(Shape):
    temperature = FloatRef.slot()

class Dashboard(Shape):
    warnings = MemIntRef.slot()

TEMP_WARN = 35.0

station = f.Seq(
    f.Race(
        # Producer: generate readings
        f.Seq(
            Sensor.temperature.set(18.0),
            Dashboard.warnings.set(0),
            f.ForRange(0, 100, f.Seq(
                Sensor.temperature.set(Sensor.temperature.get() + 0.3),
                f.Delay(0.02),
            )),
        ),
        # Consumer: react to temperature changes
        f.ReactWhile(
            Sensor.temperature.on_change(),
            Sensor.temperature.get() < 50.0,
            f.If(
                Sensor.temperature.get() > TEMP_WARN,
                f.Seq(
                    Dashboard.warnings.set(Dashboard.warnings.get() + 1),
                    f.Print("WARN", Sensor.temperature.get()),
                ),
            ),
        ),
    ),
    f.Print("Total warnings", Dashboard.warnings.get()),
)
```

## Example: Retry with Fallback

```python
import every_flow as f

fetch_with_retry = f.TryCatch(
    f.Retry(
        fetch_from_api,
        max_attempts=3,
        delay=1.0,
        backoff=2.0,
    ),
    catch=f.Seq(
        f.Log("API failed, using cache", level="warning"),
        load_from_cache,
    ),
)
```

## Writing Custom Flows

See [defining-own-flow.md](defining-own-flow.md).
