---
title: ImageRef
---

Image by url with alt text and a fit mode. Display-only, server-owned.

## kind

display

## defaults (class-level)

| field     | type                                       | default     | notes                                                                |
| --------- | ------------------------------------------ | ----------- | -------------------------------------------------------------------- |
| `src`     | `str`                                      | `""`        | image url. Empty renders a placeholder gap.                          |
| `alt`     | `str`                                      | `""`        | alt text for screen readers. Empty allowed for decorative images.    |
| `fit`     | `Literal["contain", "cover", "fill"]`      | `"contain"` | object-fit mode on the `<img>`.                                      |
| `width`   | `int | None`                               | `None`      | optional css width in px. `None` lets the layout decide.             |
| `height`  | `int | None`                               | `None`      | optional css height in px. `None` lets the layout decide.            |
| `rounded` | `bool`                                     | `False`     | when true, applies tailwind `rounded-md`.                            |

Declared as class attributes on the python `ImageRef`. Each non-base value is shipped under the mount field entry's `props` key; base defaults are omitted to keep wire frames lean.

## interactions

| op      | dir           | payload                                                                                       | nu method                                                                              | notes                                              |
| ------- | ------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `write` | server -> tab | `{"src"?: str, "alt"?: str, "fit"?: str, "width"?: int|null, "height"?: int|null, "rounded"?: bool}` | `store_src`, `store_alt`, `store_fit`, `store_size`, `store_rounded`, `store` | partial update; absent keys leave the slice as is. |

Nu methods compile to the same wire op with different payload subsets:

- `store_src(url)` -> `write {"src": url}`
- `store_alt(text)` -> `write {"alt": text}`
- `store_fit(mode)` -> `write {"fit": mode}`
- `store_size(width, height)` -> `write {"width": width, "height": height}`
- `store_rounded(flag)` -> `write {"rounded": flag}`
- `store(src, alt=..., fit=..., width=..., height=..., rounded=...)` -> `write` with all non-`None` kwargs

## wire payloads

```
// mount field entry (only when class defaults differ from base)
{"path": "HomePage.hero", "type": "ImageRef", "props": {"src": "/static/logo.png", "alt": "logo"}}

// src-only update
{"op": "write", "ref": "HomePage.hero", "payload": {"src": "/static/banner.png"}}

// fit change
{"op": "write", "ref": "HomePage.hero", "payload": {"fit": "cover"}}

// size change
{"op": "write", "ref": "HomePage.hero", "payload": {"width": 320, "height": 180}}

// combined update
{"op": "write", "ref": "HomePage.hero", "payload": {"src": "/static/avatar.png", "alt": "user", "rounded": true}}

// clear src via Nu sentinel
{"op": "write", "ref": "HomePage.hero", "payload": {"src": null}}
```

Payload is a msgpack map. Missing keys keep current slice values. Nu sentinels encode as msgpack nil; on the browser nil decodes to `""` for `src` / `alt`, `"contain"` for `fit`, `null` for `width` / `height`, `false` for `rounded`.

## renderer

`web/src/refs/image.tsx`. A plain `<img>` with tailwind `object-*` utilities driven by `fit`. Empty `src` renders an inline-block placeholder `<span>` sized by width/height (if set). `rounded` toggles `rounded-md`. No external shadcn dep.

## slice shape

```
{
  type: "ImageRef",
  value: null,
  src: string,
  alt: string,
  fit: string,
  width: number | null,
  height: number | null,
  rounded: boolean,
  write: (v: {src?, alt?, fit?, width?, height?, rounded?}) => void,
}
```

Seeded from `field.props` on mount with fallbacks `""` / `""` / `"contain"` / `null` / `null` / `false`. `write` merges partial payloads.

## edge cases

- empty payload (`{}`): no-op, slice unchanged.
- `src` is msgpack nil: stored as `""`; renderer shows the placeholder gap.
- `alt` is msgpack nil: stored as `""`.
- `fit` is msgpack nil: stored as `"contain"`.
- `fit` string outside the three known modes: stored raw; renderer falls back to `object-contain`. No error frame.
- `width` / `height` msgpack nil: stored as `null`; that axis is omitted from the inline style.
- `rounded` msgpack nil: stored as `false`.
- slot never written and no `props` on mount: selector defaults kick in, placeholder gap shown.
- broken image url: standard browser behavior (alt shown). No wire-side fallback indicator.

## non-goals

- no `append`, no `read`, no `notify`. Single image, server-owned.
- no click / hover / load interactions. A clickable image belongs to a separate `ImageButtonRef`.
- no srcset / responsive sources; single url only in v0.1.0.
- no lazy-loading flag, no priority hints.
- no caption slot; captions are a separate Ref or layout concern.
- no error frame on bad url.
- no `caps` flags on mount; deferred catalog-wide.
