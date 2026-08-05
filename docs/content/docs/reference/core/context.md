---
title: nu.context
---

The Context fabric: `ctx.attrs` (flat, name-keyed store for short-lived
primitives) and `ctx.bind`/`ctx.get` fabric bindings (typed ctx-bound
resources). Two axes, two small interaction sets.

`from nu import SetCmd, Delete, AttrExists, FabricExists`

## Attrs

Writes and existence check on the `AttrRef` axis (`ctx.attrs`). The read
itself is the Ref's dual role, not a separate query.

| Name       | Sort          | Signature              | Effect        | Meaning                                  |
| ---------- | ------------- | ----------------------- | ------------- | ----------------------------------------- |
| SetCmd     | ScalarCommand | `SetCmd(ref, value)`    | mutates(ref)  | write value to the Ref's slot in ctx.attrs |
| Delete     | ScalarCommand | `Delete(ref)`           | mutates(ref)  | remove the Ref from ctx.attrs             |
| AttrExists | ScalarQuery   | `AttrExists(ref)`       | pure          | whether the AttrRef's address is bound    |

## Fabric

Existence check on the `FabricRef` axis (`ctx.bind`/`ctx.get`). The read
itself is the Ref's dual role; only existence needs an explicit query.

| Name         | Sort        | Signature           | Effect | Meaning                              |
| ------------ | ----------- | -------------------- | ------ | ------------------------------------- |
| FabricExists | ScalarQuery | `FabricExists(ref)` | pure   | whether the FabricRef's fabric type is bound |
