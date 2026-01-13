# Location Vocabulary — Philosophy

Each layer has its own location abstraction. This is intentional.

## The Progression

```text
key → site → path → ref
```

| Layer | Term | What it is |
| ------- | ------ | ------------ |
| Storage | **key** | Raw tuple coordinates |
| Container | **site** | Hierarchical place |
| View | **path** | Typed navigation segments |
| Shape | **ref** | Declarative handle |

Each adds meaning while preserving the location abstraction.

---

## Key (Storage Layer)

A **key** is raw coordinates. Tuple of segments. Nothing more.

```python
("users", "alice", "age")
```

Keys are:

- Dumb — no hierarchy interpretation
- Fast — direct storage address
- Universal — same format across all backends

Storage speaks only keys. It doesn't know "users" contains "alice".

---

## Site (Container Layer)

A **site** is a hierarchical place. It's a key interpreted as a location in a tree.

```python
("users", "alice")  # site of alice container
("users",)          # site of users container
()                  # root site
```

Sites are:

- Structural — parent-child relationships exist
- Typed — container vs primitive distinction
- Anchored — a site can have children

The difference: a key is coordinates, a site is a place.

Same tuple, different semantics:

- Storage sees `("users", "alice")` as an address
- Container sees `("users", "alice")` as a site where alice lives, with `("users",)` as parent

---

## Path (View Layer)

A **path** is a sequence of typed navigation segments.

```python
(
    ("users", DictView),
    ("alice", DictView),
    ("tags", ListView),
    (-1, str),  # last item
)
```

Paths are:

- Typed — each segment knows its view type
- Navigable — views interpret segments (e.g., `-1` means "last")
- Protocol-aware — DictView paths vs ListView paths behave differently

Views translate paths to sites. A path segment like `-1` resolves to an actual site.

---

## Ref (Shape Layer)

A **ref** is a declarative handle to a typed location.

```python
User.profile.email        # Ref[str]
Users["alice"].tags[-1]   # Ref[str]
```

Refs are:

- Composable — chain with `.` and `[]`
- Typed — carry type information (`Ref[str]`)
- Lazy — resolve to paths when executed

Refs are what developers write. The system translates down: ref → path → site → key.

---

## Why Distinct Terms?

Clarity. Each layer operates on the same underlying tuple, but with different semantics.

When you say "key", you mean storage address.
When you say "site", you mean hierarchical place.
When you say "path", you mean typed navigation.
When you say "ref", you mean developer-facing handle.

No ambiguity about which layer you're talking about.
