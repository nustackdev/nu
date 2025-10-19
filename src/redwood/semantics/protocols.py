"""View protocol definitions.

Protocols define the capabilities that views must provide for different
access patterns.

Design Philosophy:
    - Protocols as contracts (not inheritance hierarchies)
    - Structural typing (duck typing with type safety)
    - No runtime checks (trust static analysis)
    - Composable (views can implement multiple protocols)

Usage Pattern:
    1. Views implement protocol methods
    2. Slots declare view_type at construction
    3. Refs store view_type as concrete class
    4. Operations call view methods (type-checked)
    5. Type checker verifies compatibility

Protocol Extension Pattern:
    To add new protocol (e.g., SequenceProtocol):
    1. Define protocol with required methods
    2. Document which views implement it
    3. No registration needed - structural typing

Example:
    class DictView:  # Implements MutableMappingProtocol
        def get(self, key: str) -> Any: ...
        def set(self, key: str, value: Any) -> None: ...
        def remove(self, key: str) -> None: ...
        def keys(self) -> list[str]: ...
        def __contains__(self, key: str) -> bool: ...

    # Type checker verifies DictView has all required methods
    view: MutableMappingProtocol = DictView(node, ctx)  ✓
"""
