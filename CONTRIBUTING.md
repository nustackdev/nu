# Contributing

Thank you for your interest in contributing to the project!
This guide will help you set up the development environment and follow our coding standards.

## Linting Setup

We use several tools to maintain code quality and consistency. Here's how to set them up:

### 1. Install Dependencies

First, install the required linting tools:

```bash
pip install flake8 black isort pre-commit
```

### 2. Set Up Pre-commit Hooks

We use pre-commit hooks to automatically check and format code before each commit. To set it up:

1. Install the pre-commit hooks:
   ```bash
   pre-commit install
   ```

2. The pre-commit configuration is already in the `.pre-commit-config.yaml` file in the repository root.

### 3. IDE Configuration (VS Code)

Visual Studio Code configuration is located at `.vscode/settings.json`.
If you are using any other IDE, feel free to contribute its configuration.

## Linting Guidelines

### Flake8

We use Flake8 for code linting. Our configuration is in the `.flake8` file in the repository root. Key points:

- Max line length is 88 characters (consistent with Black).
- We ignore some errors that conflict with Black or are overly restrictive.

To run Flake8 manually:

```bash
flake8 .
```

### Black

We use Black for code formatting. Our configuration is in `pyproject.toml`. To format your code:

```bash
black .
```

### isort

We use isort to sort imports. Its configuration is also in `pyproject.toml`. To sort imports:

```bash
isort .
```

## Workflow

1. Before starting work, pull the latest changes from the main branch.
2. Create a new branch for your feature or bug fix.
3. Write your code, following our coding standards.
4. Run linters and formatters (this will happen automatically if you've set up pre-commit hooks).
5. Commit your changes. The pre-commit hooks will check your code before allowing the commit.
6. Push your branch and create a pull request.

## Tips

- If the pre-commit hooks modify your files, you'll need to stage and commit those changes.
- You can run `pre-commit run --all-files` at any time to check all files in the repository.
- If you need to bypass the pre-commit hooks for any reason, use `git commit --no-verify`. Use this sparingly!

Happy coding!
