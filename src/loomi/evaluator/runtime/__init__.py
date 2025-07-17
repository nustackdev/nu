from __future__ import annotations

from concurrent.futures import Future
from typing import Any, Callable, Protocol


class Runtime(Protocol):
    def execute(
        self,
        method: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]: ...

    def execute_distributed(
        self,
        method: Callable,
        args_list: list[tuple[Any, ...]],
        kwargs_list: list[dict[str, Any]] | None = None,
    ) -> list[Future[Any]]: ...
