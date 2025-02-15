from _typeshed import Incomplete

from loomi.app.base import SyncApp as SyncApp
from loomi.app.handlers.tasks import SyncOperationProtocol as SyncOperationProtocol

from ..exceptions import OperationError as OperationError
from .base_operation import BaseOperation as BaseOperation
from .logger import logger as logger

class SequenceOperation(BaseOperation):
    operations: Incomplete
    delay: Incomplete
    continue_on_error: Incomplete
    def __init__(
        self, *operations: SyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> None: ...
    def execute(self, app: SyncApp) -> None: ...
