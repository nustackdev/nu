"""Expose a plain Python Calculator as a Nu Service via nustd.service."""

import asyncio

import nu
import nustd


class Calculator:
    def __init__(self) -> None:
        self.total = 0.0

    def add(self, a: float, b: float) -> float:
        return a + b

    def mul(self, a: float, b: float) -> float:
        return a * b

    def bump(self, by: float) -> float:
        self.total += by
        return self.total

    def reset(self) -> None:
        self.total = 0.0

    def range(self, n: int):
        for i in range(n):
            yield i * i


class Calc(nu.Service):
    add = nustd.service.QueryRef.method()
    mul = nustd.service.QueryRef.method()
    bump = nustd.service.ActionRef.method()
    reset = nustd.service.CommandRef.method()
    squares = nustd.service.StreamQueryRef.method(name="range")


app = nu.With(
    nustd.service.bind(Calc, target=Calculator()),
    body=nu.Sequential(
        nu.print(Calc.add(a=2, b=3)),
        nu.print(Calc.mul(a=6, b=7)),
        nu.print(Calc.bump(by=10)),
        nu.print(Calc.bump(by=5)),
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
