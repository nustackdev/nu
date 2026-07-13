---
title: MarkdownRef
---

Rendered markdown block. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field   | type  | default | notes                                                                                |
| ------- | ----- | ------- | ------------------------------------------------------------------------------------ |
| `value` | `str` | `""`    | source markdown. Shipped under mount field `props` only when overridden (non-empty). |

Declared as a plain class attribute on the python `MarkdownRef`. A subclass that sets a non-empty default has its value seeded into the browser slice on `mount` without an explicit `write`. The empty default is omitted from the mount payload to keep wire frames lean.

## interactions

| op      | dir           | payload | nu method | notes                                       |
| ------- | ------------- | ------- | --------- | ------------------------------------------- |
| `write` | server -> tab | `str`   | `store`   | full replace. msgpack nil decodes to `""`.  |

Single op, full replace. No partial-update, no append. The browser re-renders the markdown each time the slice value changes.

## wire payloads

```
// mount field entry (only when the class default is non-empty)
{"path": "HomePage.body", "type": "MarkdownRef", "props": {"value": "# hello\n\nworld"}}

// server pushes a new value
{"op": "write", "ref": "HomePage.body", "payload": "# title\n\n- a\n- b"}

// server clears via Nu sentinel
{"op": "write", "ref": "HomePage.body", "payload": null}
```

## renderer

`web/src/refs/markdown.tsx`. A `<div>` carrying tailwind `prose prose-sm max-w-none` wraps a `<ReactMarkdown>` from `react-markdown`. Commonmark only, no remark plugins, no `rehype-raw`: any inline html in the source renders as literal text (no script injection vector via the wire).

## slice shape

```
{
  type: "MarkdownRef",
  value: string,
  write: (v: string | null) => void,
}
```

Seeded from `props.value` when present, else `""`. `write` replaces `value` outright; nil maps to `""`.

## edge cases

- payload is msgpack nil: slice `value` becomes `""`, renderer emits an empty `<div>`.
- slot never written and no `props`: selector returns `""`, renders an empty `<div>`.
- malformed markdown: react-markdown is forgiving and renders the best parse it can. No error frame, no server-side validation.
- raw html in the source: not rendered as html. Appears as literal text since `rehype-raw` is not wired.
- payload that is neither string nor nil: coerced via `String(v)` in the slice. No error frame.
- very large strings: no chunking, no virtualization. The host page is responsible for not pushing megabytes into a single slot.

## non-goals

- no `append`, no `read`, no `notify`. Markdown source is server-owned and replaced wholesale.
- no raw html passthrough. The wire stays safe by default.
- no syntax highlighting for fenced code blocks in v0.1.0. Plain `<code>` via the prose classes.
- no math, mermaid, or custom remark plugins.
- no click / hover interactions. Links route via standard browser behaviour.
- no per-instance theming. Restyle by patching `prose` at the host app's tailwind config.
- no `caps` flags on mount; deferred catalog-wide.
