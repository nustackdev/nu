"""Engine layer: the generic execution driver.

- ``Runtime`` - generic per-execution driver; the toolkit lives as methods on it.
- ``Budget`` - per-execution thread pool + concurrency gate; owned by Runtime.
- ``into_loop`` - stateless coroutine-runner for sync code.
- ``safely_closing`` / ``safely_aclosing`` - generator-finalization helpers.
"""

from nu2.engine.execute.budget import Budget
from nu2.engine.execute.driver import Runtime
from nu2.engine.execute.loop import into_loop, safely_aclosing, safely_closing


__all__ = [
    "Budget",
    "Runtime",
    "into_loop",
    "safely_aclosing",
    "safely_closing",
]
