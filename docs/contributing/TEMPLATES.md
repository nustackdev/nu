# Templates

## pyproject.toml - Extension Package (ext/)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "eb-foo"
version = "0.1.0"
description = "Foo for everybase"
readme = "README.md"
license = "MIT"
authors = [{ name = "Gor Arakelyan", email = "gorarkln@gmail.com" }]
requires-python = ">=3.10"
dependencies = ["everybase>=0.1.0"]
keywords = ["every", "foo"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Repository = "https://github.com/everyabc/everybase"

[tool.hatch.build.targets.wheel]
packages = ["src/eb_foo"]
```

## README.md - Extension Package

```markdown
# eb-foo

Brief description.

## Install

\`\`\`bash
pip install eb-foo
\`\`\`

## Usage

\`\`\`python
from eb_foo import Thing
\`\`\`

## Development

Part of [everybase](https://github.com/everyabc/everybase).

\`\`\`bash
uv run pytest ext/eb-foo
\`\`\`
```

## conftest.py - Package Tests

```python
"""Package-specific fixtures."""

import pytest


@pytest.fixture
def sample_data():
    """Example fixture."""
    return {"key": "value"}
```
