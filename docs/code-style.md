# Code Style


## Build Commands
- Install: `poetry install`
- Lint: `poetry run pre-commit run --all-files`
- Type Check: `poetry run pyright`
- Run example: `poetry run python examples/task_management/app.py`

## Code Style
- Line length: 100 characters
- Format: Use Black (`black .`) and isort (`isort .`)
- Python version: 3.12
- Imports style: isort with black profile (grouped by first-party and third-party)
- First-party modules: `loomi`, `loomistd`, `loomiverse`
- Type annotations: Required for function parameters and return values
- Naming: snake_case for variables/functions, PascalCase for classes
- Error handling: Use async/await consistently, follow existing patterns for error propagation
- Documentation: Docstrings for public classes and methods

### Module Organization

- Each major component gets its own directory
- Public API and implementations are carefully separated:
    - Each component has its own exceptions and logger
    - Common types live in root `types.py`
    - Common type_vars live in root `type_vars.py`
    - Module’s base class is called `base.py`
    - Modules protocols live in `protocols.py`

### Exception Guidelines

1. **Don't Hide Useful Information**
    - Never catch and discard exceptions silently
    - Don't wrap exceptions when they already provide sufficient context
    - Preserve the original traceback when re-raising
2. **Keep the Exception Hierarchy Clean**
    - Each layer should have its own semantically meaningful exceptions
    - Don't expose implementation details through exceptions
    - Use custom exceptions for domain-specific errors
3. **Be Specific About What You Catch**
    - Never use bare `except:`
    - Catch only exceptions you can actually handle
    - Let unknown exceptions propagate up
4. Do's and Don'ts:
    - Use Custom Exceptions for Domain Logic
    - Preserve Exception Context
    - Handle Known Exceptions Explicitly
    - Add Context When it Helps
    - Clean up resources on error
    - Don't Catch Generic Exceptions
    - Don't Rewrap Library Exceptions Without Adding Value
    - Don't Swallow Exceptions Without Logging
    - Don't Mix Business Logic with Exception Handling
5. **Documentation**:
    - Document all possible exceptions in method docstrings
    - Include error conditions and meanings
    - Provide recovery suggestions where applicable

### Logging

Usage

```python
from .logger import logger

# In code:
logger.debug("Detailed operation info")
logger.info("Important state changes")
logger.warning("Recoverable issues")
logger.error("Operation failures")
```

Module implementation at `loomi/logging`, provides `get_logger` method to set up logger for each module.

```
/state
	/_ogger.py
	...
```

logger.py:

```python
from logging import Logger

from loomi.logging import get_logger

logger: Logger = get_logger(__name__)
```

Then use:

```python
from ._logger import logger
```

Guidelines:
1. **Log Levels**:
    - DEBUG: Detailed debugging information
    - INFO: Important state changes, operations
    - WARNING: Recoverable issues
    - ERROR: Operation failures
2. **Context**:
    - Include relevant keys/identifiers
    - Log operation outcomes
    - Include error details
3. **Performance**:
    - Lazy string formatting
    - Appropriate log levels
    - No sensitive data

### Type-Safety

- **Use `from __future__ import annotations`**
    - Put at the top of every typed Python file
    - Enables forward references without string literals
    - Makes all annotations lazy-evaluated
    - Reduces import overhead
- **Use built-in collection syntax**
    - `list[str]` instead of `List[str]`
    - `dict[str, int]` instead of `Dict[str, int]`
    - `tuple[int, ...]` instead of `Tuple[int, ...]`
    - Cleaner syntax, better performance, reduces imports
- **Use union operator `|`**
    - `str | int` instead of `Union[str, int]`
    - `str | None` instead of `Optional[str]`
    - More readable, especially in nested types
    - Example: `dict[str, list[int | str]]`
- **Use `TypeAlias` for type definitions**
    - `from typing_extensions import TypeAlias`
    - `JsonDict: TypeAlias = dict[str, "JsonValue"]`
    - Makes type alias explicit and self-documenting
    - Enables better IDE support
- **Use `@runtime_checkable` with Protocols**
    - Enables `isinstance()` checks with Protocol classes
    - Only use when runtime checking is needed
    - Adds runtime overhead, so use judiciously
- **Use `TypedDict` for dictionary structures**
    - `NotRequired[]` for optional fields (Python 3.11+)
    - Better than `total=False` for mixed required/optional fields
    - Provides clear contract for dict structures
- **Use `TypeVar` with descriptive names**
    - Include constraints when possible: `TypeVar("T", str, bytes)`
    - Use bounds for class hierarchies: `TypeVar("T", bound=BaseClass)`
    - Add `_co`/`_contra` suffix for variance: `TypeVar("T_co", covariant=True)`
- **Use `Final` for constants**
    - `from typing import Final`
    - `MAX_RETRIES: Final = 3`
    - Ensures values cannot be reassigned
- **Use `Literal` for exact values**
    - `Mode = Literal["r", "w", "a"]`
    - Better than enums for simple cases
    - Enables exhaustive pattern matching
- **Use `type[T]` for class references**
    - Instead of `Type[T]` from typing module
    - `def create(cls: type[T]) -> T: ...`
    - For annotating class objects/metaclasses
- **Use `*` and `/` for positional arguments**
    - `/` marks positional-only parameters
    - `*` marks keyword-only parameters
    - Example: `def f(x: int, /, y: str, *, z: bool) -> None: ...`
- **Use `TypeGuard` for type narrowing**
    - `def is_str_list(val: list[Any]) -> TypeGuard[list[str]]: ...`
    - Helps type checker understand runtime checks
    - Better than type casting
- **Use `@overload` for multiple signatures**
    - When function accepts multiple distinct type patterns
    - Provides better type inference for callers
    - Must be followed by concrete implementation
- **Use `@property` with return type annotations**
    - `@property`
    - `def name(self) -> str: ...`
    - Helps catch incorrect return types
- **Use `Callable` with full type information**
    - `Callable[[int, str], bool]` for function types
    - Include all parameter and return types
    - Use `...` for unknown parameter lists: `Callable[..., None]`
- **Use `ParamSpec` for decorator types**
    - `from typing import ParamSpec`
    - Preserves signature of decorated functions
    - Better than `Callable[..., Any]`
- **Use `Never` for impossible returns**
    - Functions that never return normally
    - Example: infinite loops, error raising functions
    - `def fail() -> Never: raise RuntimeError()`
- **Use `NewType` for type distinction**
    - Create distinct types for same base type
    - `UserId = NewType("UserId", int)`
    - Prevents mixing of semantically different values
- **Use `Annotated` for additional metadata**
    - Add validation info, documentation, etc.
    - `name: Annotated[str, "User's full name"]`
    - Useful for generating documentation/schemas
- **Use `__all__` for exports in each module

### Code Documentation

1. **Docstrings**:
    - All public methods/classes
    - Args/returns/raises
    - Usage examples
    - Type hints
2. **Comments**:
    - Complex logic explanation
    - Warning about edge cases
    - Implementation notes
