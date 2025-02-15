from typing import Any, Callable

from _typeshed import Incomplete

from loomi.app.base import SyncApp as SyncApp

from ..exceptions import OperationError as OperationError
from .base_operation import BaseOperation as BaseOperation
from .logger import logger as logger

class FunctionOperation(BaseOperation):
    func: Incomplete
    name: Incomplete
    def __init__(self, func: Callable[..., Any], *, name: str | None = None) -> None: ...
    def execute(self, app: SyncApp) -> None: ...
