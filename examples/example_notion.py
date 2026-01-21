"""Example: Notion datatable operations with everybase Shapes.

This example demonstrates how to use NotionTable shapes for
declarative, ORM-like access to Notion databases.

Prerequisites:
    1. Create a Notion integration at https://www.notion.so/my-integrations
    2. Get your integration token (secret_xxx)
    3. Share a database with your integration
    4. Get the database ID from the URL

Usage:
    export NOTION_API_KEY="secret_xxx"
    export NOTION_DATABASE_ID="your-database-id"
    python examples/example_notion.py
"""

from __future__ import annotations

import os

from everybase.notion import (
    CheckboxSlot,
    EmailSlot,
    NotionContext,
    NotionTable,
    NumberSlot,
    SelectSlot,
    TextSlot,
    TitleSlot,
)


# =============================================================================
# DEFINE SCHEMAS (like everybase Shapes)
# =============================================================================


class Users(NotionTable):
    """Users database schema."""

    database_id = os.environ.get("NOTION_DATABASE_ID", "2ed7cf006d4f8025828cd4f3bd373e82")

    # Define columns as slots
    name = TitleSlot()  # Primary title column
    email = EmailSlot()
    bio = TextSlot()
    score = NumberSlot()
    status = SelectSlot()
    active = CheckboxSlot()


class Orders(NotionTable):
    """Orders database schema (example of second table)."""

    database_id = os.environ.get("NOTION_ORDERS_DB", "orders-database-id")

    order_id = TitleSlot()
    amount = NumberSlot()
    status = SelectSlot()


# =============================================================================
# EXAMPLES
# =============================================================================


def example_shape_access() -> None:
    """Demonstrate Shape-based ref access patterns."""
    print("=== Shape-based Ref Access ===\n")

    # Row ref via subscript
    row = Users["some-page-id"]
    print(f"Row ref: {row}")

    # Cell refs via attribute access
    name_cell = row.name
    email_cell = row.email
    score_cell = row.score
    print(f"Name cell: {name_cell}")
    print(f"Email cell: {email_cell}")
    print(f"Score cell: {score_cell}")

    # Operations (lazy - not executed yet)
    get_name = row.name.get()
    get_email = row.email.get()
    set_score = row.score.set(100)
    print(f"\nGet name op: {get_name}")
    print(f"Get email op: {get_email}")
    print(f"Set score cmd: {set_score}")

    # Chained access
    chained = Users["page-id"].status.get()
    print(f"Chained: {chained}")

    # Add row command
    add_cmd = Users.add_row(
        name="Alice",
        email="alice@example.com",
        score=95,
        status="Active",
    )
    print(f"\nAdd row cmd: {add_cmd}")

    # Remove row command
    remove_cmd = Users["page-id"].remove()
    print(f"Remove cmd: {remove_cmd}")


def example_term_programming() -> None:
    """Demonstrate term programming patterns (similar to example_shape.py)."""
    print("\n=== Term Programming Patterns ===\n")

    # Like: Market.signals["vix"].set(23.5).execute(ctx)
    # We have: Users["page-id"].score.set(95).execute(ctx)

    print("# Setting values")
    print('Users["page-id"].score.set(95).execute(ctx)')
    print('Users["page-id"].email.set("new@example.com").execute(ctx)')

    print("\n# Getting values")
    print('score = Users["page-id"].score.get().execute(ctx)')
    print('email = Users["page-id"].email.get().execute(ctx)')

    print("\n# Adding rows (like Market.orders.append(...))")
    print("Users.add_row(name='Bob', email='bob@example.com').execute(ctx)")

    print("\n# Removing rows")
    print('Users["page-id"].remove().execute(ctx)')

    print("\n# Query all rows")
    print("all_users = Users.execute(ctx)")


def example_with_real_api() -> None:
    """Run actual API calls if credentials are set."""
    print("\n=== Real API Example ===\n")

    api_key = (
        "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"  # os.environ.get("NOTION_API_KEY")
    )
    database_id = "2ed7cf006d4f8025828cd4f3bd373e82"  # https://www.notion.so/2ed7cf006d4f8025828cd4f3bd373e82?v=2ed7cf006d4f8083a673000cbcab4a32&source=copy_linkos.environ.get("NOTION_DATABASE_ID")

    if not api_key or database_id == "your-database-id":
        print("Set NOTION_API_KEY and NOTION_DATABASE_ID to run this example")
        print("  export NOTION_API_KEY='secret_xxx'")
        print("  export NOTION_DATABASE_ID='abc123...'")
        return

    with NotionContext.create(api_key=api_key) as ctx:
        # Query all rows
        print("Fetching all rows from Users table...")
        rows = Users.execute(ctx)
        print(f"Found {len(rows)} rows\n")

        # Show first few rows
        for i, row_data in enumerate(rows[:3]):
            page_id = row_data["id"]
            print(f"Row {i + 1}: {page_id[:8]}...")

            # Get name (title)
            try:
                name = Users[page_id].name.get().execute(ctx)
                print(f"  name: {name}")
            except KeyError:
                print("  name: (not found)")

            # Get email if exists
            try:
                email = Users[page_id].email.get().execute(ctx)
                print(f"  email: {email}")
            except KeyError:
                print("  email: (not found)")

        Users.add_row(name="Alice Grace", email="alice2@example.com").execute(ctx)


def example_cross_table() -> None:
    """Example of working with multiple tables."""
    print("\n=== Cross-Table Access ===\n")

    print("# Define multiple tables")
    print("""
class Users(NotionTable):
    database_id = "users-db-id"
    name = TitleSlot()
    email = EmailSlot()

class Orders(NotionTable):
    database_id = "orders-db-id"
    order_id = TitleSlot()
    amount = NumberSlot()
""")

    print("# Access each table the same way")
    print('user_name = Users["user-page-id"].name.get().execute(ctx)')
    print('order_amount = Orders["order-page-id"].amount.get().execute(ctx)')

    print("\n# Cross-table operations (conceptual)")
    print("# Like: Notion.users.traded.set(Chain.data.symbols.get())")
    print('Users["uid"].score.set(Orders["oid"].amount.get()).execute(ctx)')


if __name__ == "__main__":
    print("Notion Shape Example")
    print("=" * 60)

    example_shape_access()
    example_term_programming()
    example_cross_table()

    print("\n" + "=" * 60)
    example_with_real_api()

    print("\n" + "=" * 60)
    print("Done!")
