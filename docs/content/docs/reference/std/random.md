---
title: nu.std.random
---

No central class - free functions over the global RNG. Every function is non-deterministic (reads the RNG) so its atom is never constant-folded. Deferred until the effect model lands: `seed`, `shuffle`, `getstate`/`setstate`.

`from nu.std.random import randint, choice`

| Name          | Sort        | Signature               | Effect  | Meaning                                             |
| ------------- | ----------- | -------------------------- | ------- | ------------------------------------------------------ |
| random        | ScalarQuery | `random()`                 | non-det | float in `[0.0, 1.0)`                                   |
| uniform       | ScalarQuery | `uniform(a, b)`             | non-det | float in `[a, b]`                                       |
| randint       | ScalarQuery | `randint(a, b)`             | non-det | int `N` with `a <= N <= b`                              |
| randrange     | ScalarQuery | `randrange(start, stop)`    | non-det | int in `range(start, stop)`                             |
| getrandbits   | ScalarQuery | `getrandbits(k)`            | non-det | non-negative int with `k` random bits                  |
| choice        | ScalarQuery | `choice(seq)`               | non-det | one random element of `seq` -> `Any`                    |
| choices       | ScalarQuery | `choices(population, k)`    | non-det | `k`-sized list drawn with replacement -> `List`         |
| sample        | ScalarQuery | `sample(population, k)`     | non-det | `k`-sized list drawn without replacement -> `List`      |
| gauss         | ScalarQuery | `gauss(mu, sigma)`          | non-det | Gaussian draw                                            |
| normalvariate | ScalarQuery | `normalvariate(mu, sigma)`  | non-det | normal draw                                              |
| expovariate   | ScalarQuery | `expovariate(lambd)`        | non-det | exponential draw with rate `lambd`                      |
| triangular    | ScalarQuery | `triangular(low, high)`     | non-det | triangular draw between `low` and `high`                |
