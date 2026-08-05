---
title: nu.ray
---

Distributed compute fabric backed by Ray. Locations are actor processes,
addresses are hashable tags, and the interaction is `Teleport` (ship a Nu
tree to a tagged actor and await its result). `RayCluster` and `RayService`
are lifecycle resources that slot into `Provide` / `ProvideList` /
`ProvideDict`; `RayClusterRef` and `RayServiceRef` read them off `ctx`.

## Cluster

`from nu.ray import RayCluster, RayClusterRef`

| Name          | Sort     | Signature                                                                   | Effect     | Meaning                                                                                     |
| ------------- | -------- | --------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| RayCluster    | Resource | `RayCluster(address="auto", *, ignore_reinit_error=True, **init_kwargs)`    | lifecycle  | connects to or starts a ray cluster; `cleanup` calls `ray.shutdown()` only if it owned init |
| RayClusterRef | FabricRef | `RayClusterRef()`                                                          | read       | resolves the bound `RayCluster` on ctx; singleton, no tag                                   |

## Service

`from nu.ray import RayService, RayServiceRef`

| Name          | Sort      | Signature                                                                                                                                    | Effect     | Meaning                                                                                                              |
| ------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------- |
| RayService    | Resource  | `RayService(ctx_builder=None, *, init=None, node=None, actor_name=None, num_cpus=None, num_gpus=None, max_restarts=0, lifetime=None)`         | lifecycle  | spawns one remote actor per bracket hosting a Nu `Context` + tree executor; `aexecute(tree, attrs=None)` routes to it |
| RayServiceRef | FabricRef | `RayServiceRef(tag=UNSET)`                                                                                                                    | read       | resolves the `RayService` bound at `tag` on ctx; tag forwards verbatim to `ctx.get(RayService, *tag)`                |

Pass exactly one of `init` (a `_LifecycleBracket`, typically `With(...)`,
entered once inside the actor and held live for its lifetime) or
`ctx_builder` (a callable returning a `Context` or awaitable). Actor
options (`node`, `actor_name`, `num_cpus`, `num_gpus`, `max_restarts`,
`lifetime`) forward to `_RayServiceActor.options(**opts).remote()`.

Tag shapes match how `Provide` / `ProvideList` / `ProvideDict` bound the
service: no tag for a bare `Provide` singleton, int index for
`ProvideList`, dict key for `ProvideDict`. `RayServiceRef(("ledger", 0))`
resolves the tuple-keyed entry.

## Interaction

`from nu.ray import Teleport`

| Name     | Sort   | Signature                                       | Effect | Meaning                                                                                            |
| -------- | ------ | ----------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| Teleport | Policy | `Teleport(body, *, target=UNSET, carry=False)`  | remote | ship `body` as a term to the `RayService` at `target` and await its result; async runtime required |

Transparent policy: removing `Teleport` does not change what is computed,
only where it runs. Cardinality is preserved; a stream-rooted body is
collapsed to the remote result and yielded once. `target=UNSET` resolves
the untagged singleton; `target=None` is a legitimate tag. Set `carry=True`
to copy the parent's `ctx.attrs` onto the remote Context before executing.
