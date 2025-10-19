from .term import RValue


class Operation[T](RValue):
    """A *pure* RValue — produces a value deterministically without side effects.

    Operations correspond to reads, computations, or logical expressions.
    They can be cached or composed freely.
    """

    def __init__(self) -> None:
        super().__init__()
        self.meta.is_pure = True
        self.meta.has_side_effects = False

    @abstractmethod
    def evaluate(self, context: C) -> T:
        """Evaluate the operation and return a value."""
        ...
