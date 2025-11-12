# Location Vocabulary

Redwood has three location abstractions, each at a different layer:

## Keys

Keys (Storage/Tree) are raw tuple addresses: ("users", "alice", "age"). Direct, dumb, and fast.
The storage layer speaks only keys.

Examples:

```python
# Alice key
("/", "users", "alice")
```

## Paths

Paths (View) add navigation semantics.

A path is a sequence of typed segments leading to a destination.
Views interpret paths, translating domain keys (like -1 for "last item") into storage keys.
Paths understand protocols - DictView paths vs ListView paths behave differently.

Examples:

```python
# Path to users dict
(
    ("users", DictView),
)

# Path to alice's data dict
(
    ("users", DictView),
    ("alice", DictView),
)

# Path to the last item of alice's tags list
(
    ("users", DictView),
    ("alice", DictView),
    ("tags", ListView),
    (-1, str),
)
```

## Refs

Refs (Shape) are declarative handles to typed locations. They compose (User.profile.email), carry type information (Ref[str]), and resolve to paths when executed.
Refs are what developers write - the system translates them down through paths to keys.

The hierarchy is semantic layering: keys → paths → refs, each adding meaning while maintaining the location abstraction.

```python
User.profile.email

Users["alice"].tags[-1]
```
