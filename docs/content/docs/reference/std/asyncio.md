---
title: nu.std.asyncio
---

No central class - `asyncio` is orchestration (`gather`, `wait`, `create_task`, `run`), and that's already what Nu Flows are. The one leaf primitive Flows can't express is the non-blocking sleep.

`from nu.std.asyncio import sleep`

| Name  | Sort        | Signature      | Effect              | Meaning                                             |
| ----- | ----------- | -------------- | -------------------- | --------------------------------------------------- |
| sleep | ScalarQuery | `sleep(delay)` | non-det, async-only | suspend the coroutine without blocking the loop (mirrors `asyncio.sleep`); sync sibling is `nu.std.time.sleep` |
