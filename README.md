# Loomi

🌟 Transform scrappy python scripts into reliable and maintainable applications.

## Core Concepts

### Application Architecture

The `App` class is your app's command center, providing:

- **Smart Lifecycle Management**: Resources initialize and clean up automatically
- **Intuitive Dependency Injection**: Services find their dependencies without manual wiring
- **Centralized State**: One source of truth with automatic persistence
- **Elegant Task Orchestration**: Complex workflows made simple

### Services

Services in Loomi are self-managing components that:

- **Initialize Automatically**: Dependencies resolve themselves in the correct order
- **Connect Effortlessly**: The `Attach` decorator handles all the wiring
- **Handle Lifecycle Events**: Setup and cleanup happen at the right time
- **Stay Type-Safe**: Catch interface mismatches at development time
- **Embrace Async**: Built for modern async/await patterns

### State Management

A powerful state system that gives you:

- **Type-Safe State**: Catch data errors before they happen
- **Automatic Persistence**: State survives restarts without extra code
- **Transaction Safety**: Atomic updates with automatic rollback
- **Real-time Updates**: Subscribe to changes with type-safe callbacks
- **Async by Default**: Handle state changes efficiently

### Workflows

- **Composable Workflows**: Complex patterns built through sequential, parallel, conditional, and reactive composition of simpler operations
- **First-Class Operations**: Encapsulated units of asynchronous behavior with standardized interfaces for state access and lifecycle management
- **Consistent Operation Design**: All operations follow uniform patterns for arguments, error handling, and concurrency control
- **Logical Organization**: Operations grouped into intuitive categories (Core, Flow Control, Timing, Collection, Reactive) for easy discovery

## Installation

You need to have poetry installed. For that run `pip install poetry`. Poetry by default puts your env files in the user directory, which might be inconvenient for the VScode to pick up the right python to work with. To automatically create poetry env in the project's directory (and VScode to auto-pickup the right python) run the following `poetry config virtualenvs.in-project true`. It is a suggested practice to have this command in your bashrc.

```bash
git clone ...
cd loomi
poetry install
```

## Examples

Explore getting started examples in the `examples` directory.
