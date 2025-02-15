from _typeshed import Incomplete

from loomi.app.base import AsyncApp as AsyncApp
from loomi.app.handlers.tasks import AsyncOperationProtocol as AsyncOperationProtocol

from ..exceptions import OperationError as OperationError
from .base_operation import BaseOperation as BaseOperation
from .logger import logger as logger

class RepeatOperation(BaseOperation):
    operation: Incomplete
    times: Incomplete
    while_key: Incomplete
    max_iterations: Incomplete
    delay: Incomplete
    ignore_errors: Incomplete
    def __init__(
        self,
        operation: AsyncOperationProtocol,
        *,
        times: int | None = None,
        while_key: str | tuple[str, ...] | None = None,
        max_iterations: int | None = None,
        delay: float = 0,
        ignore_errors: bool = False,
    ) -> None: ...
    async def execute(self, app: AsyncApp) -> None: ...
