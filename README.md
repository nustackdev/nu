# Loomi

🌟 Transform scrappy python scripts into reliable and maintainable applications.

## About

Turn this:

```python
# Messy script with global state and manual dependency management
redis_client = Redis(host="localhost")
db = Database(host="localhost", redis=redis_client)

def process_data(data):
    # Manual error handling, no type safety
    if db.is_valid(data):
        redis_client.set("data", data)
    
async def main():
    # Manual lifecycle management
    await db.connect()
    await process_data({"key": "value"})
    await db.disconnect()
```

Into this:

```python
class DataProcessor(AsyncApp):
    # Automatic dependency injection and lifecycle management
    db = UseService(DatabaseService, db_spec)
    cache = UseService(RedisService, cache_spec)
    
    # Type-safe state management
    data = UseModel(state, dict[str, str])
    
    async def process(self, input_data: dict[str, str]):
        async with self.state.transaction():
            await self.data.set(input_data)  # Automatic persistence
```

Check out `/examples` directory for more examples.

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

### Models

Smart data containers that provide:

- **Runtime Type Safety**: Catch data errors as they happen
- **Automatic Defaults**: Values initialize correctly every time
- **Flexible Persistence**: Store what you need, where you need it
- **Change Tracking**: Know what changed and when
- **Schema Updates**: Evolve your data model safely

## Installation

You need to have poetry installed. For that run `pip install poetry`. Poetry by default puts your env files in the user directory, which might be inconvenient for the VScode to pick up the right python to work with. To automatically create poetry env in the project's directory (and VScode to auto-pickup the right python) run the following `poetry config virtualenvs.in-project true`. It is a suggested practice to have this command in your bashrc.

```bash
git clone ...
cd loomi
poetry install
```

## Examples

Explore complete, production-ready examples in our `examples` directory:

- Task Management System
- More examples coming soon!

### Running Examples

To run the `task_management` example:

```bash
cd examples/task_management
poetry run python app.py
```