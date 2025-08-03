"""
Loomi App Module - Declarative workflow applications.

This module provides App classes for building declarative workflow applications
with automatic dependency injection for state, evaluator, and logger services.

Classes:
    SyncApp: Synchronous app with workflow capabilities
    AsyncApp: Asynchronous app with workflow capabilities

Example:
    ```python
    from loomi import AsyncApp

    class DataProcessingApp(AsyncApp):
        def define(self):
            return self.ev.Sequence(
                self.ev.Function(self.load_data),
                self.ev.Map(
                    self.ev.Function(self.process_item),
                    items_path=("items",),
                    max_concurrency=4
                ),
                self.ev.Function(self.save_results)
            )

        async def load_data(self, context):
            data = await fetch_data()
            async with self.s.at("items").with_dict_view() as view:
                await view.store(data)
            await self.log.info(f"Loaded {len(data)} items")

    # Usage
    async with DataProcessingApp(spec) as app:
        await app.start()
    ```
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loomicore.attach import Attach
from loomicore.resource import AsyncResource, SyncResource

if TYPE_CHECKING:
    from loomi._behaviors.evaluator import Context, Evaluator, Expression
    from loomi._behaviors.logger import AsyncLoggerProtocol, SyncLoggerProtocol
    from loomi._behaviors.state import State

__all__ = [
    "AppBase",
    "SyncApp",
    "AsyncApp",
]


class AppBase(ABC):
    """
    Ultra-thin base for all apps with dependency injection.

    Provides dependency injection via Attach descriptors and convenience aliases.
    All operational logic is handled by LoomiCore and injected dependencies.

    Type Parameters:
        StateT: State protocol implementation type
        EvaluatorT: Evaluator protocol implementation type
        LoggerT: Logger protocol implementation type
    """

    # Attach descriptors - resolved by LoomiCore dependency injection
    state: State = Attach()
    evaluator: Evaluator = Attach(optional=True)
    logger: AsyncLoggerProtocol | SyncLoggerProtocol = Attach(optional=True)

    def evaluate(
        self,
        expression: "Expression",
        context: "Context",
    ) -> None:
        """
        Evaluate an expression in the context of this app.

        Args:
            expression: The expression to evaluate
            context: The execution context
        """
        self.evaluator.evaluate(self, expression, context)

    @abstractmethod
    def define(self) -> "Expression":
        """
        Define the app's workflow.

        This method should return the root operation that represents
        the complete workflow for this app. The evaluator will execute
        this operation tree.

        Returns:
            Root operation of the workflow

        Example:
            ```python
            def define(self):
                return self.ev.Sequence(
                    self.ev.Function(self.initialize),
                    self.ev.Map(
                        self.ev.Function(self.process_item),
                        items_path=("items",)
                    )
                )
            ```
        """
        pass


class SyncApp(AppBase, SyncResource):
    """
    Synchronous App with state, evaluator, and logger.

    Ultra-thin wrapper that provides:
    - Dependency injection via Attach descriptors
    - Workflow definition via define() method
    - Synchronous execution via start() method
    - Full type safety and autocompletion

    The app inherits from SyncResource, so it gets all LoomiCore
    resource management features (lifecycle, deduplication, etc.)
    automatically.

    Example:
        ```python
        from loomi import SyncApp

        class FileProcessorApp(SyncApp):
            def define(self):
                return self.ev.Sequence(
                    self.ev.Function(self.scan_files),
                    self.ev.Map(
                        self.ev.Function(self.process_file),
                        items_path=("files",)
                    ),
                    self.ev.Function(self.cleanup)
                )

            def scan_files(self, context):
                files = scan_directory("./input")
                with self.s.at("files").with_dict_view() as view:
                    view.store(files)
                self.log.info(f"Found {len(files)} files")

            def process_file(self, context):
                filename = context["map_key"]
                # Process file logic
                self.log.info(f"Processed {filename}")

        # Usage
        with FileProcessorApp(spec) as app:
            app.start()
        ```
    """

    pass


class AsyncApp(AppBase, AsyncResource):
    """
    Asynchronous App with state, evaluator, and logger.

    Ultra-thin wrapper that provides:
    - Async dependency injection via Attach descriptors
    - Async workflow definition via define() method
    - Async execution via start() method
    - Full type safety and autocompletion

    The app inherits from AsyncResource, so it gets all LoomiCore
    async resource management features automatically.

    Example:
        ```python
        from loomi import AsyncApp

        class WebScraperApp(AsyncApp):
            def define(self):
                return self.ev.Sequence(
                    self.ev.Function(self.load_urls),
                    self.ev.Map(
                        self.ev.Sequence(
                            self.ev.Function(self.fetch_page),
                            self.ev.Function(self.extract_data)
                        ),
                        items_path=("urls",),
                        max_concurrency=10
                    ),
                    self.ev.Function(self.save_results)
                )

            async def load_urls(self, context):
                urls = await get_urls_to_scrape()
                async with self.s.at("urls").with_dict_view() as view:
                    await view.store(urls)
                await self.log.info(f"Loaded {len(urls)} URLs")

            async def fetch_page(self, context):
                url = context["map_key"]
                # Fetch and process page
                await self.log.info(f"Fetched {url}")

        # Usage
        async with WebScraperApp(spec) as app:
            await app.start()
        ```
    """

    pass
