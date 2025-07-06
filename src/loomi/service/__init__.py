"""
Loomi Service Module - Lightweight services with logging.

This module provides Service classes for building lightweight services
with automatic dependency injection for logger services. Services are
simpler than Apps and don't include workflow evaluation capabilities.

Classes:
    SyncService: Synchronous service with logging
    AsyncService: Asynchronous service with logging

Example:
    ```python
    from loomi.service import AsyncService

    class DatabaseService(AsyncService):
        async def setup(self):
            self.connection = await connect_to_db()
            await self.log.info("Database connected")

        async def cleanup(self):
            await self.connection.close()
            await self.log.info("Database disconnected")

        async def query(self, sql: str):
            await self.log.debug(f"Executing: {sql}")
            result = await self.connection.execute(sql)
            await self.log.info(f"Query returned {len(result)} rows")
            return result

    # Usage
    async with DatabaseService(spec) as db:
        users = await db.query("SELECT * FROM users")
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from loomicore import AsyncResource, SyncResource
from loomicore.attach import Attach

if TYPE_CHECKING:
    from loomi.logger.interface.logger import AsyncLoggerProtocol, SyncLoggerProtocol

__all__ = [
    "ServiceBase",
    "SyncService",
    "AsyncService",
]

# Type variable for generics
LoggerT = TypeVar("LoggerT")


class ServiceBase(Generic[LoggerT]):
    """
    Ultra-thin base for all services with logging dependency injection.

    Provides dependency injection for logger via Attach descriptor and
    convenience alias. All operational logic is handled by LoomiCore
    and injected dependencies.

    Type Parameters:
        LoggerT: Logger protocol implementation type
    """

    # Attach descriptor - resolved by LoomiCore dependency injection
    logger: LoggerT  # = Attach()

    # Convenience alias for shorter syntax
    @property
    def log(self) -> LoggerT:
        """Short alias for logger."""
        return self.logger


class SyncService(ServiceBase["SyncLoggerProtocol"], SyncResource):
    """
    Synchronous service with logging.

    Ultra-thin wrapper that provides:
    - Dependency injection for logger via Attach descriptor
    - Synchronous logging capabilities
    - Full type safety and autocompletion
    - All LoomiCore resource management features

    Services are lighter than Apps - they don't include state management
    or workflow evaluation capabilities, just logging and resource lifecycle.

    Example:
        ```python
        from loomi.service import SyncService

        class FileManagerService(SyncService):
            def setup(self):
                self.base_path = Path("./data")
                self.base_path.mkdir(exist_ok=True)
                self.log.info(f"FileManager initialized at {self.base_path}")

            def cleanup(self):
                # Cleanup logic here
                self.log.info("FileManager cleaned up")

            def save_file(self, filename: str, content: str):
                filepath = self.base_path / filename
                filepath.write_text(content)
                self.log.info(f"Saved file: {filename}")
                return filepath

            def load_file(self, filename: str) -> str:
                filepath = self.base_path / filename
                content = filepath.read_text()
                self.log.info(f"Loaded file: {filename}")
                return content

        # Usage
        with FileManagerService(spec) as fs:
            fs.save_file("test.txt", "Hello World")
            content = fs.load_file("test.txt")
        ```
    """

    pass


class AsyncService(ServiceBase["AsyncLoggerProtocol"], AsyncResource):
    """
    Asynchronous service with logging.

    Ultra-thin wrapper that provides:
    - Async dependency injection for logger via Attach descriptor
    - Asynchronous logging capabilities
    - Full type safety and autocompletion
    - All LoomiCore async resource management features

    Services are lighter than Apps - they don't include state management
    or workflow evaluation capabilities, just logging and resource lifecycle.

    Example:
        ```python
        from loomi.service import AsyncService

        class HttpClientService(AsyncService):
            async def setup(self):
                self.session = aiohttp.ClientSession()
                await self.log.info("HTTP client initialized")

            async def cleanup(self):
                await self.session.close()
                await self.log.info("HTTP client closed")

            async def get(self, url: str) -> dict:
                await self.log.debug(f"GET request to {url}")
                async with self.session.get(url) as response:
                    data = await response.json()
                    await self.log.info(f"GET {url} -> {response.status}")
                    return data

            async def post(self, url: str, data: dict) -> dict:
                await self.log.debug(f"POST request to {url}")
                async with self.session.post(url, json=data) as response:
                    result = await response.json()
                    await self.log.info(f"POST {url} -> {response.status}")
                    return result

        # Usage
        async with HttpClientService(spec) as client:
            data = await client.get("https://api.example.com/users")
            result = await client.post("https://api.example.com/users", {"name": "John"})
        ```
    """

    pass
