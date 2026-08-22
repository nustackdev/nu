"""Dynamic Nu tree evaluation: pick a Nu term, evaluate it in the same runtime."""

import nu


class State(nu.Shape):
    program = nu.mem.StrRef.slot()
    result = nu.mem.IntRef.slot()


REGISTRY: dict[str, nu.Nu] = {
    "double": State.result.set(State.result * 2),
    "square": State.result.set(State.result * State.result),
}

program = (
    State.result.set(7)
    >> State.program.set("double")
    >> nu.Eval(nu.Literal(REGISTRY["double"]))
    >> nu.print(nu.str(State.result))
    >> State.program.set("square")
    >> nu.Eval(nu.Literal(REGISTRY["square"]))
    >> nu.print(nu.str(State.result))
)


if __name__ == "__main__":
    ctx = nu.Context().bind(dict, {}, State)
    nu.run(program, ctx)
