from .term import RValue


class Command(RValue):
    """An *impure* RValue — performs an effect or mutation when evaluated.

    Commands correspond to writes, deletions, or stateful updates. They
    express *intent* to change the system.
    """

    def __init__(self) -> None:
        super().__init__()
        self.meta.is_pure = False
        self.meta.has_side_effects = True

    @abstractmethod
    def evaluate(self, context: C) -> None:
        """Execute the command's side effect."""
        ...
