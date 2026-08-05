---
title: nu.std.uuid
---

Mirrors `uuid` 1-1: `UUID` is the class (a Form); `uuid1`/`uuid3`/`uuid4`/`uuid5` are the module-level generator functions.

`from nu.std.uuid import UUID, uuid4`

### Value type

| Name | Sort | Signature   | Effect | Meaning                                                                                    |
| ---- | ---- | ------------ | ------ | ---------------------------------------------------------------------------------------------- |
| UUID | Form | `UUID.of(...)` (via `from_str`/`from_bytes`/`from_int`) | pure | UUID; `.version`/`.variant`/`.time`/`.clock_seq`/`.node`, `.hex`/`.urn`/`.bytes`/`.bytes_le`/`.int_`, comparison |

### Functions

| Name  | Sort        | Signature                          | Effect  | Meaning                                       |
| ----- | ----------- | ------------------------------------ | ------- | ------------------------------------------------ |
| uuid4 | ScalarQuery | `uuid4()`                            | non-det | random UUID (version 4)                          |
| uuid1 | ScalarQuery | `uuid1(node=None, clock_seq=None)`   | non-det | host/time UUID (version 1)                       |
| uuid3 | ScalarQuery | `uuid3(namespace, name)`             | pure    | name-based MD5 UUID (version 3)                  |
| uuid5 | ScalarQuery | `uuid5(namespace, name)`             | pure    | name-based SHA-1 UUID (version 5)                |
