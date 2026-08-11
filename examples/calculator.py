"""Expose a plain Python Calculator as a Nu Service via nu.service."""

import asyncio

import nu


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
    add = nu.service.QueryRef.method()
    mul = nu.service.QueryRef.method()
    bump = nu.service.ActionRef.method()
    reset = nu.service.CommandRef.method()
    squares = nu.service.StreamQueryRef.method(name="range")


app = nu.With(
    nu.service.bind(Calc, target=Calculator()),
    body=nu.Sequential(
        nu.print(Calc.add(a=2, b=3)),
        nu.print(Calc.mul(a=6, b=7)),
        nu.print(Calc.bump(by=10)),
        nu.print(Calc.bump(by=5)),
    ),
)


if __name__ == "__main__":
    asyncio.run(nu.arun(app))
