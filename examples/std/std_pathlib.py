"""nu.std.pathlib seed: ``pathlib`` paths as Forms, the v2 way.

Imported like the stdlib: ``from nu.std.pathlib import Path``. Backed by
``PurePath``, so only the pure (no filesystem I/O) operations are modeled.
Property reads reuse core GetAttrQuery; method calls bind the unbound PurePath
methods; comparison reuses the core atoms. Each entry prints run result, term
type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.pathlib import Path


ctx = Context()

# 1. Build a path from segments (PathOf), then read its name (GetAttrQuery).
e1 = Path.of("usr", "local", "bin").name()
print(run(e1, ctx)[0], type(e1), e1)

# 2. Read the suffix property (GetAttrQuery).
e2 = Path.of("archive.tar.gz").suffix()
print(run(e2, ctx)[0], type(e2), e2)

# 3. Swap the suffix (factory atom over the unbound method), then as_posix.
e3 = Path.of("report.txt").with_suffix(".md").as_posix()
print(run(e3, ctx)[0], type(e3), e3)

# 4. Join with the / operator (joinpath atom), then as_posix.
e4 = (Path.of("etc") / "nginx" / "nginx.conf").as_posix()
print(run(e4, ctx)[0], type(e4), e4)

# 5. The parent directory (GetAttrQuery returning a path Form), then as_posix.
e5 = Path.of("a", "b", "c").parent().as_posix()
print(run(e5, ctx)[0], type(e5), e5)

# 6. as_posix on a built path.
e6 = Path.of("var", "log", "syslog").as_posix()
print(run(e6, ctx)[0], type(e6), e6)

# 7. Comparison via the < operator (core LtQuery).
e7 = Path.of("a") < Path.of("b")
print(run(e7, ctx)[0], type(e7), e7)
