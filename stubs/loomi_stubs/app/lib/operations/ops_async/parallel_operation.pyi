from _typeshed import Incomplete

from loomi.app.base import AsyncApp as AsyncApp
from loomi.app.handlers.tasks import AsyncOperationProtocol as AsyncOperationProtocol

from ..exceptions import OperationError as OperationError
from .base_operation import BaseOperation as BaseOperation
from .logger import logger as logger

class ParallelOperation(BaseOperation):
    operations: Incomplete
    max_concurrent: Incomplete
    timeout: Incomplete
    ignore_errors: Incomplete
    def __init__(
        self,
        *operations: AsyncOperationProtocol,
        max_concurrent: int | None = None,
        timeout: float | None = None,
        ignore_errors: bool = False,
    ) -> None: ...
    async def execute(self, app: AsyncApp) -> None: ...
