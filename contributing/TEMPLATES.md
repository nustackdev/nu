# Templates

## pyproject.toml - Core Package (abc/)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "every"
version = "0.1.0"
description = "Core primitives for every"
readme = "README.md"
license = "MIT"
authors = [{ name = "Your Name", email = "you@example.com" }]
requires-python = ">=3.10"
dependencies = ["attrs>=23.0.0"]
keywords = ["every", "core"]
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
packages = ["src/every"]
```

## pyproject.toml - Standard Package (std/)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "every-datetime"
version = "0.1.0"
description = "DateTime types for every"
readme = "README.md"
license = "MIT"
authors = [{ name = "Your Name", email = "you@example.com" }]
requires-python = ">=3.10"
dependencies = ["every>=0.1.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/every_datetime"]
```

## pyproject.toml - Extension Package (pkgs/)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "every-notion"
version = "0.1.0"
description = "Notion integration for every"
readme = "README.md"
license = "MIT"
authors = [{ name = "Your Name", email = "you@example.com" }]
requires-python = ">=3.10"
dependencies = [
    "every>=0.1.0",
    "notion-client>=2.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/every_notion"]
```

## README.md - Package

```markdown
# every-foo

Brief description.

## Install

\`\`\`bash
pip install every-foo
\`\`\`

## Usage

\`\`\`python
from every_foo import Thing
\`\`\`

## Development

Part of [everybase](https://github.com/everyabc/everybase).

\`\`\`bash
make test-pkg PKG=std/every_foo
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
