"""Exception hierarchy for DSL operations.

All DSL-specific exceptions inherit from DSLError, which inherits from RedwoodError
for consistency with the rest of the codebase.
"""

from redwood.exceptions import RedwoodError


class DSLError(RedwoodError):
    """Base exception for all DSL-related errors.

    Root of the DSL exception hierarchy - catch this for generic DSL error handling.
    """

    pass


class DSLEvaluationError(DSLError):
    """Error during term evaluation.

    Raised when a term cannot be evaluated due to runtime issues not covered
    by more specific exception types.

    Examples:
        - Circular dependency detected
        - Maximum evaluation depth exceeded
        - Invalid evaluation context
    """

    pass


class DSLTypeError(DSLError):
    """Schema or type violation.

    Raised when there's a type mismatch between expected and actual types,
    or when schema constraints are violated.

    Examples:
        - Expected int, got str in schema validation
        - Invalid primitive type specified in Field
        - Type mismatch in domain type construction
    """

    pass


class DSLPathError(DSLError):
    """Invalid path construction or resolution.

    Raised when path operations fail due to structural issues.

    Examples:
        - Attempting to navigate through a primitive
        - Invalid field name in schema
        - Path resolution fails due to dynamic index evaluation error
    """

    pass


class DSLSchemaError(DSLError):
    """Schema definition error.

    Raised when schema is incorrectly defined or contains invalid specifications.

    Examples:
        - Field missing both primitive and view specification
        - Field has both primitive and view (mutual exclusion)
        - Invalid schema nesting
    """

    pass


class DSLViewError(DSLError):
    """View protocol or operation error.

    Raised when view operations fail or when attempting unsupported operations
    on a view.

    Examples:
        - Calling .set() on immutable view
        - View doesn't support required protocol
        - Invalid view method invocation
    """

    pass
