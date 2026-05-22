"""Compilation: Term -> Program.

The phase that turns an immutable Term (description) into a Program (runnable
artifact). Three acts, one verb:

- index             - walk the Term in preorder, assign dense nids, fill the
                      structural columns (terms, children, parent_id, path_of,
                      id_of).
- attribute sweeps  - one pass per computed attribute in schema order,
                      synthesized (bottom-up) or inherited (top-down).
- emit              - reverse preorder; each Term's compile/acompile builds a
                      thunk that captures its child thunks.

Output is a Program: an indexed Term with attribute and thunk columns ready
for a Runtime to drive. No IR, no optimizer.
"""

from nu2.engine.compilation.program import Path, Program, compile


__all__ = ["Path", "Program", "compile"]
