---
title: nu.invisibles
---

Transparent remote objects: local calls, remote execution. Pure transport over
TCP or Unix socket. No new refs, no new interactions. Method calls on a client
proxy travel the wire and land on the server-side bound fabric, dispatched by
the same `FabricRef` machinery that works locally.

## Server

`from nu.invisibles import InvisiblesServer`

| Name             | Sort            | Signature                                                                                            | Effect        | Meaning                                                                              |
| ---------------- | --------------- | ---------------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- |
| InvisiblesServer | FabricLifecycle | `InvisiblesServer(target, address, *, target_tag=None, transport="tcp", executor="simple", dispatcher="inline")` | starts thread | look up the bound `target` fabric on ctx, serve it on `address` in a background thread |

Transport is `"tcp"` or `"unix"`. Executor is `"simple"` or `"threaded"`
(how connections are accepted). Dispatcher is `"inline"`, `"async"`,
`"threaded"`, or `"shared"` (how method calls run).

## Client

`from nu.invisibles import InvisiblesClient`

| Name             | Sort            | Signature                                                                                                          | Effect         | Meaning                                                          |
| ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------ | -------------- | ----------------------------------------------------------------- |
| InvisiblesClient | FabricLifecycle | `InvisiblesClient(address, *, transport="tcp", timeout=5.0, max_retries=3, bg_serve=False, buffered_iteration=True)` | opens conn     | connect with retry, fetch the remote root, expose it as `.root`   |

`.root` is a transparent proxy for the remote fabric. Attribute access and
method calls go over the wire synchronously.

## Bracket

`from nu.invisibles import InvisiblesProxy`

| Name            | Sort            | Signature                                                                                                                        | Effect            | Meaning                                                                                    |
| --------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------- |
| InvisiblesProxy | Bracket         | `InvisiblesProxy(target, body=None, *, address, tag=None, transport="tcp", timeout=5.0, max_retries=3, bg_serve=False, buffered_iteration=True)` | binds proxy       | provision an `InvisiblesClient` and bind its `.root` on ctx under `target` in one step      |

Async-only bracket. Collapses the two-Provide-plus-rebind pattern into one
line: connect to an invisibles-hosted fabric and let the rest of the tree talk
to it as the plain target type.
