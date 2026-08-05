---
title: nu.std.itertools
---

Gap-fill over Nu core: members core already covers (`map`/`filter`/`zip`/`sorted`/`enumerate`/`reversed`/sums) are not repeated. Every member is a hand-written `StreamQuery` atom except `tee`.

`from nu.std.itertools import chain, islice, count`

### Infinite sources

| Name   | Sort        | Signature             | Effect | Meaning                                    |
| ------ | ----------- | ----------------------- | ------ | -------------------------------------------- |
| count  | StreamQuery | `count(start=0, step=1)` | pure | unbounded arithmetic stream; bound with `islice` |
| cycle  | StreamQuery | `cycle(iterable)`       | pure   | repeat a source forever                     |
| repeat | StreamQuery | `repeat(elem, times=None)` | pure | yield `elem` `times` times, or forever    |

### Pure combinators

| Name                          | Sort        | Signature                                        | Effect | Meaning                                     |
| ----------------------------- | ----------- | -------------------------------------------------- | ------ | ---------------------------------------------- |
| chain                         | StreamQuery | `chain(*iterables)`                                | pure   | concatenate sources end to end                 |
| chain_from_iterable           | StreamQuery | `chain_from_iterable(iterable)`                    | pure   | flatten an iterable of iterables one level     |
| islice                        | StreamQuery | `islice(iterable, *args)`                          | pure   | lazy slice (`stop` \| `start,stop` \| `start,stop,step`) |
| compress                      | StreamQuery | `compress(data, selectors)`                        | pure   | keep `data` where `selectors` is truthy        |
| pairwise                      | StreamQuery | `pairwise(iterable)`                               | pure   | overlapping consecutive pairs                  |
| batched                       | StreamQuery | `batched(iterable, n)`                             | pure   | tuples of up to `n` items                      |
| zip_longest                   | StreamQuery | `zip_longest(*iterables, fillvalue=None)`          | pure   | zip to the longest, padding short sources      |
| product                       | StreamQuery | `product(*iterables, repeat=1)`                    | pure   | cartesian product                              |
| permutations                  | StreamQuery | `permutations(iterable, r=None)`                   | pure   | `r`-length ordered arrangements                |
| combinations                  | StreamQuery | `combinations(iterable, r)`                        | pure   | `r`-length sorted subsequences                 |
| combinations_with_replacement | StreamQuery | `combinations_with_replacement(iterable, r)`       | pure   | `r`-length subsequences allowing repeats       |

### Higher-order

| Name       | Sort        | Signature                          | Effect | Meaning                                                        |
| ---------- | ----------- | ------------------------------------ | ------ | ------------------------------------------------------------------ |
| takewhile  | StreamQuery | `takewhile(predicate, iterable)`     | pure   | yield while `predicate` holds, stop at the first falsy             |
| dropwhile  | StreamQuery | `dropwhile(predicate, iterable)`     | pure   | skip while `predicate` holds, then yield the rest                  |
| filterfalse| StreamQuery | `filterfalse(predicate, iterable)`   | pure   | keep items where `predicate` is falsy                              |
| accumulate | StreamQuery | `accumulate(iterable, func=None)`    | pure   | running accumulation (sum by default, or a Nu term over acc/item)   |
| starmap    | StreamQuery | `starmap(function, iterable)`       | pure   | apply `function` to unpacked tuple items                           |
| groupby    | StreamQuery | `groupby(iterable, key=None)`        | pure   | group consecutive items by key -> `(key, tuple(group))` pairs      |

### tee

| Name | Sort        | Signature          | Effect | Meaning                                                     |
| ---- | ----------- | -------------------- | ------ | ---------------------------------------------------------------- |
| tee  | ScalarQuery | `tee(iterable, n=2)` | pure   | split into `n` independent iterators -> `Any` holding a tuple (not a stream) |
