---
title: CodeBlockRef
---

Preformatted code block with optional language label. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field       | type   | default | notes                                                                            |
| ----------- | ------ | ------- | -------------------------------------------------------------------------------- |
| `code`      | `str`  | `""`    | source code text. Rendered verbatim inside a `<pre><code>`. Whitespace preserved. |
| `language`  | `str`  | `""`    | informational label (e.g. `"python"`, `"rust"`). No syntax highlighting in v1.    |
| `show_copy` | `bool` | `True`  | render a copy-to-clipboard button. Browser-only affordance; no server notify.    |

Declared as plain class attributes on the python `CodeBlockRef`. Empty defaults are omitted from the mount payload: only keys that differ from `""` / `True` ride in on `props`. The browser slice seeds from the props dict, falling back to the same defaults if absent.

## interactions

| op      | dir           | payload                            | nu method        | notes                                                |
| ------- | ------------- | ---------------------------------- | ---------------- | ---------------------------------------------------- |
| `write` | server -> tab | `{code?: str, language?: str}`     | `store`          | partial dict; missing keys leave slice fields alone. |
| `write` | server -> tab | `{code: str}`                      | `store_code`     | full replace of the code text. nil decodes to `""`.  |
| `write` | server -> tab | `{language: str}`                  | `store_language` | replaces the language label. nil decodes to `""`.    |

One wire op (`write`) with a dict payload. The nu-side methods just shape the dict. No `append`, no `read`, no `notify`. The copy button does not emit a frame.

`show_copy` is reachable via the generic `write` op (any key in the dict is merged) but has no dedicated nu method in v1; treat it as a class default in practice.

## wire payloads

```
// mount field entry (only when at least one default differs from the seed)
{"path": "HomePage.snippet", "type": "CodeBlockRef", "props": {"code": "print(1)\n", "language": "python"}}

// server pushes a full snippet
{"op": "write", "ref": "HomePage.snippet", "payload": {"code": "fn main() {}\n", "language": "rust"}}

// server changes only the language label
{"op": "write", "ref": "HomePage.snippet", "payload": {"language": "rust"}}

// server clears the code via Nu sentinel
{"op": "write", "ref": "HomePage.snippet", "payload": {"code": null}}

// server toggles the copy button off
{"op": "write", "ref": "HomePage.snippet", "payload": {"show_copy": false}}
```

## renderer

`web/src/refs/code-block.tsx`. A `<div>` wraps a small header (language label on the left, copy button on the right, both conditional) and a `<pre><code>` body. shadcn / radix not required; a plain `<button>` with `onClick={() => navigator.clipboard.writeText(code)}` handles the copy. Tailwind classes: `font-mono text-sm bg-muted rounded p-3 overflow-x-auto`. No external highlighter.

## slice shape

```
{
  type: "CodeBlockRef",
  code: string,
  language: string,
  show_copy: boolean,
  write: (payload: {code?: string|null, language?: string|null, show_copy?: boolean|null}) => void,
}
```

Seeded from `props.code` / `props.language` / `props.show_copy` when present, else the class defaults (`""`, `""`, `true`). `write` merges any subset of keys; nil on `code` / `language` coerces to `""`; nil on `show_copy` coerces to the class default (`true`).

## edge cases

- payload missing keys: only declared keys mutate the slice; others stay put.
- `code` or `language` is msgpack nil: slice field becomes `""`.
- `show_copy` is msgpack nil: slice field falls back to the class default (`true`).
- slot never written and no `props`: selector returns the defaults (`""`, `""`, `true`). With empty `code` and empty `language`, the renderer still emits an empty `<pre>` and a copy button that copies an empty string.
- header is fully hidden when both `language === ""` and `show_copy === false`.
- very long single lines: the body uses `overflow-x-auto`; no soft-wrap.
- copy on browsers without `navigator.clipboard` (insecure context): the call rejects silently; no server notify, no error frame.

## non-goals

- no syntax highlighting in v1. The `language` field is a label only. Adding a highlighter (`shiki`, `prismjs`, `highlight.js`) is deferred since it grows the bundle and pulls in a per-language theme story. Revisit once the gallery stabilizes.
- no line numbers, no copy-success toast, no notify back to the server on copy.
- no diff / unified-patch rendering.
- no inline-code variant (use a markdown ref or plain text for that).
- no append-stream of partial code chunks; one `write` per replace.
- no `caps` flags on mount; deferred catalog-wide.
