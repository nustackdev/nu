# NavRef

Structural Ref bound to `window.history` + `window.location`. Lives on an Index. Bidirectional: the host writes new URIs via `history.pushState` / `replaceState`; the user pressing back / forward fires a `notify` back to the host.

For the end-to-end design and the "many stores" framing see the case study in the Go space: `projects/nu/stack/nudle/navigation.md`.

## kind

structural. zero body output. mirrors the current URI into the zustand slice so renderers and other refs can subscribe to URI changes uniformly.

## defaults (class-level)

none. on mount the browser slice seeds `value` from `window.location`. no `mount_props`.

## interactions

| op       | dir           | payload                                                                       | nu method                              | notes                                                                |
| -------- | ------------- | ----------------------------------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------- |
| `write`  | server -> tab | `str` or `{"action": "push" \| "replace" \| "back" \| "forward", "uri"?: str}` | `store`, `replace`, `back`, `forward` | bare string = push (shorthand). dict carries an action tag.          |
| `read`   | server -> tab | -                                                                             | `aread`                                | server asks current URI; the slice's `get()` returns the mirror.     |
| `notify` | tab -> server | `str` (current URI)                                                           | `changed`                              | fires on `popstate` (user back/forward, or programmatic navigation). |

Four nu methods compile to the same wire op with different payload shapes:

- `store(uri)` -> `write "<uri>"`. Pushes onto history (bare string shorthand).
- `replace(uri)` -> `write {"action": "replace", "uri": "<uri>"}`. Uses `history.replaceState` -- URL bar updates without growing the back-button stack.
- `back()` -> `write {"action": "back"}`. Calls `window.history.back()`. The browser will fire `popstate` if the navigation succeeds, which round-trips to the server as a `notify`.
- `forward()` -> `write {"action": "forward"}`. Calls `window.history.forward()`. Same notify behavior as `back()`.

Riding all four on the existing `write` op keeps the protocol surface frozen. The slice inspects the payload shape to dispatch.

## wire payloads

```
// mount field entry (server -> tab, inside the mount payload)
{"path": "nav", "type": "NavRef"}

// push (bare string, back-compat shorthand)
{"op": "write", "ref": "nav", "payload": "/feed"}

// push (explicit)
{"op": "write", "ref": "nav", "payload": {"action": "push", "uri": "/feed"}}

// replace
{"op": "write", "ref": "nav", "payload": {"action": "replace", "uri": "/feed"}}

// back
{"op": "write", "ref": "nav", "payload": {"action": "back"}}

// forward
{"op": "write", "ref": "nav", "payload": {"action": "forward"}}

// server-initiated read
{"op": "read", "ref": "nav", "id": "<uuid>"}
// reply (tab -> server) re-uses the read op id
{"op": "read", "ref": "nav", "payload": "/feed", "id": "<uuid>"}

// user back/forward (tab -> server)
{"op": "notify", "ref": "nav", "payload": "/"}
```

## renderer

`web/src/refs/nav.tsx`. The component returns `null`. All behaviour lives in the slice factory.

## slice shape

```
{
  type: "NavRef",
  value: string,                                                  // mirror of current URI
  write: (v: string | {action?: string, uri?: string}) => void,   // dispatches push/replace/back/forward
  get:   () => string,                                            // current mirror, falls back to window.location
  dispose: () => void,                                            // removes the popstate listener
}
```

On mount the factory:

1. reads `window.location` to seed `value`.
2. installs a `popstate` listener that mirrors the new URI and emits `notify`.

`dispose` removes the listener. The store calls it on unmount and re-mount; without it, multiple mounts would stack listeners and double-notify.

## edge cases

- `write` with bare string equal to the current URI: skips `pushState` to avoid duplicate history entries.
- `write` with `{"action": "push" | "replace"}` and missing / null `uri`: treated as `"/"`.
- `write` with `{"action": "back"}` at the start of history: no-op in the browser; no notify.
- `write` with `{"action": "forward"}` at the end of history: same as above, browser no-op.
- `write` with an unknown action string: logged as a warning, no error frame, no state change.
- `write` with `null`: treated as `"/"` push.

## non-goals

- no `<a href>` interception. Anchor clicks still trigger a hard reload (case C in the case study).
- no path patterns (`/orders/:id`). Exact-string matches only -- routing convention is host-side.
- no query-string helpers (`with_query`, `merge_query`, ...). The host already has full access to the URI string; helpers, if useful, live in host-side code, not on the Ref.
- no initial `aread` on connect. The host opts in explicitly.
- no `pop` / stack inspection -- browsers do not expose the history stack.
