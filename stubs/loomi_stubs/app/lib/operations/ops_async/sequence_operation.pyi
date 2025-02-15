from _typeshed import Incomplete

from loomi.app.base import AsyncApp as AsyncApp
from loomi.app.handlers.tasks import AsyncOperationProtocol as AsyncOperationProtocol

from ..exceptions import OperationError as OperationError
from .base_operation import BaseOperation as BaseOperation
from .logger import logger as logger

class SequenceOperation(BaseOperation):
    operations: Incomplete
    delay: Incomplete
    continue_on_error: Incomplete
    def __init__(
        self, *operations: AsyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> None: ...
    async def execute(self, app: AsyncApp) -> None: ...
