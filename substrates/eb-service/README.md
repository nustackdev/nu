# eb-service

Service substrate for everybase.

Provides refs that point to Python in-memory objects (service clients) and a declarative access interface for their methods. A service is a resource registered in Context as a handle — that's the key difference between everybase Values (which wrap data) and Services (which wrap live objects with callable methods).

## Concepts

- **ServiceRef** — ref term that resolves a service client from context via `ctx.get(SERVICE_CLS)`. Lives in expression trees. Full Ref — can hold `method()` descriptors directly.
- **Service** — declarative entry point (like Shape for ShapeRef). Users subclass this, declare methods with `method()` descriptors. Never instantiated. Creates a ServiceRef subclass behind the scenes.

## Usage

```python
from eb_service import Service
from everybase import Context
from everybase.abc import IntValue, DictValue, method


class SolanaClient:
    async def getSlot(self):
        ...

class Solana(Service):
    SERVICE_CLS = SolanaClient
    get_slot = method(IntValue, "getSlot")
    get_balance = method(DictValue, "getBalance")

# Bind service client to context
ctx = Context().with_handle(SolanaClient, SolanaClient())

# Class-level access builds lazy term trees
slot = await Solana.get_slot().execute(ctx)
```

`Solana.get_slot()` produces:

```
IntValue
  └─MethodCallCmd(.getSlot)
    └─_SolanaRef
```

At execution, `_SolanaRef.fetch(ctx)` resolves `ctx.get(SolanaClient)` and the method call is dispatched on the returned client.

## Development

Part of [everybase](https://github.com/everyabc/everybase).
