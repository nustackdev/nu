"""nu.std.uuid seed: a typed UUID surface built the v2 way.

Imported like the stdlib: ``from nu.std.uuid import UUID, uuid4`` (or
``import nu.std.uuid as uuid``). ``UUID`` is the access surface; constructors
are new atoms (core can't build a UUID); accessors and comparisons reuse core
interactions (GetAttrQuery, EqQuery, ...). No FuncCall escape hatch. Each entry
prints run result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.uuid import UUID, uuid4, uuid5


ctx = Context()

# A fixed UUID so the run is reproducible.
NS = "12345678-1234-5678-1234-567812345678"

# 1. Construct from a hex string (UuidFromStrQuery atom).
e1 = UUID.from_str(NS)
print(run(e1, ctx)[0], type(e1), e1)

# 2. Read a component back (a v5 UUID has a real version) - reuses GetAttrQuery.
e2 = uuid5(UUID.from_str(NS), "nu").version()
print(run(e2, ctx)[0], type(e2), e2)

# 3. Convert to a hex string - also GetAttrQuery, wrapped as a StrForm.
e3 = UUID.from_str(NS).hex()
print(run(e3, ctx)[0], type(e3), e3)

# 4. Compare two UUIDs - reuses the core EqQuery atom.
e4 = UUID.from_str(NS).eq(UUID.from_str(NS))
print(run(e4, ctx)[0], type(e4), e4)

# 5. A version-5 name-based UUID (module-level uuid5, mirroring the stdlib).
e5 = uuid5(UUID.from_str(NS), "nu")
print(run(e5, ctx)[0], type(e5), e5)

# 6. A random UUID (module-level uuid4) - non-deterministic, fresh each run.
e6 = uuid4()
print(run(e6, ctx)[0], type(e6), e6)
