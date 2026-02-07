# eb-notion

Notion integration for everybase. Provides Shape-based declarative access to Notion databases.

## Install

```bash
pip install eb-notion
```

## Usage

```python
from eb_notion import NotionContext, NotionTable, TitleSlot, EmailSlot

class Users(NotionTable):
    database_id = "your-database-id"
    name = TitleSlot()
    email = EmailSlot()

with NotionContext.create(api_key="secret_xxx") as ctx:
    Users.add_row(name="Alice", email="alice@example.com").execute(ctx)
```

## Development

Part of [everybase](https://github.com/everyabc/everybase).

```bash
make test-pkg PKG=pkgs/eb_notion
```
