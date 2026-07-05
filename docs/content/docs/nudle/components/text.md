---
title: TextRef
---

Plain-text paragraph or short body string. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field   | type  | default | notes                                                                              |
| ------- | ----- | ------- | ---------------------------------------------------------------------------------- |
| `value` | `str` | `""`    | initial text. Shipped under mount field `props` only when overridden (non-empty).  |

Declared as a plain class attribute on the python `TextRef`. A subclass that sets a non-empty default has its value seeded into the browser slice on `mount` without an explicit `write`. The empty default is omitted from the mount payload to keep wire frames lean.

## interactions

| op      | dir           | payload | nu method | notes                                              |
| ------- | ------------- | ------- | --------- | -------------------------------------------------- |
| `write` | server -> tab | `str`   | `store`   | full replace. msgpack nil decodes to `""`.         |

Single op, full replace. No partial-update semantics: the whole string is the unit of change.

## wire payloads

```
// mount field entry (only when the class default is non-empty)
{"path": "HomePage.body", "type": "TextRef", "props": {"value": "hello"}}

// server pushes a new value
{"op": "write", "ref": "HomePage.body", "payload": "the quick brown fox"}

// server clears via Nu sentinel
{"op": "write", "ref": "HomePage.body", "payload": null}
```

## renderer

`web/src/refs/text.tsx`. A `<p>` with `whitespace-pre-wrap` so newline characters in the string render as line breaks without the server shipping html. No markdown, no inline formatting.

## slice shape

```
{
  type: "TextRef",
  value: string,
  write: (v: string | null) => void,
}
```

Seeded from `props.value` when present, else `""`. `write` replaces `value` outright; nil maps to `""`.

## edge cases

- payload is msgpack nil: slice `value` becomes `""`.
- slot never written and no `props`: selector returns `""`, renders an empty `<p>`.
- multi-line strings render via `whitespace-pre-wrap`; React text nodes are not parsed as html, so no escaping concerns.
- no max length on the wire. Truncation, ellipsis, line-clamping are css concerns left to the host page.
- payload that is neither string nor nil: stored raw on the slice; the selector's cast yields whatever React renders. No error frame.

## non-goals

- no `append`, no `read`, no `notify`. Body copy is server-owned and replaced wholesale.
- no markdown, no inline html, no link auto-detection. That belongs to `MarkdownRef`.
- no variants, sizes, or inline styling. Headings use `HeadingRef`; labels use `BadgeRef`.
- no click / hover interactions.
- no `caps` flags on mount; deferred catalog-wide.
