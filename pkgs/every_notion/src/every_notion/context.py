"""Notion execution context.

Provides HTTP client for Notion API operations.
"""

from __future__ import annotations

import logging
from typing import Any

import attrs
import httpx

from every import Context


__all__ = [
    "NotionContext",
]

logger = logging.getLogger(__name__)

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


@attrs.frozen
class NotionContext(Context):
    """Execution context for Notion operations.

    Provides HTTP client configured for Notion API access.

    Attributes:
        api_key: Notion integration token
        client: HTTP client for API requests
    """

    api_key: str
    client: httpx.Client = attrs.field(factory=httpx.Client)

    @classmethod
    def create(cls, api_key: str) -> NotionContext:
        """Create a new NotionContext with configured HTTP client.

        Args:
            api_key: Notion integration token (secret_xxx)

        Returns:
            Configured NotionContext
        """
        client = httpx.Client(
            base_url=NOTION_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": NOTION_API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        return cls(api_key=api_key, client=client)

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> NotionContext:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ----- Low-level API methods -----

    def get_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve database metadata."""
        response = self.client.get(f"/databases/{database_id}")
        response.raise_for_status()
        return response.json()

    def query_database(
        self,
        database_id: str,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Query database pages (rows)."""
        payload: dict[str, Any] = {}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts

        response = self.client.post(f"/databases/{database_id}/query", json=payload)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Retrieve a page (row)."""
        response = self.client.get(f"/pages/{page_id}")
        response.raise_for_status()
        return response.json()

    def create_page(
        self,
        database_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new page (row) in database."""
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        response = self.client.post("/pages", json=payload)
        response.raise_for_status()
        return response.json()

    def update_page(
        self,
        page_id: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Update page properties."""
        payload = {"properties": properties}
        response = self.client.patch(f"/pages/{page_id}", json=payload)
        response.raise_for_status()
        return response.json()

    def archive_page(self, page_id: str) -> dict[str, Any]:
        """Archive (soft-delete) a page."""
        payload = {"archived": True}
        response = self.client.patch(f"/pages/{page_id}", json=payload)
        response.raise_for_status()
        return response.json()
