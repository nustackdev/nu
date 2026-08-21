"""Bitwise atoms: Python's bit-level operators.

Maps Python's bitwise operators onto Nu ScalarQueries over integers. Pure
compute; no Context effect of their own.

Operators to cover (Python -> Nu):
- ``&`` -> ``BitAnd``, ``|`` -> ``BitOr``, ``^`` -> ``BitXor``
- ``~`` -> ``BitNot`` (unary)
- ``<<`` -> ``LShift``, ``>>`` -> ``RShift``

Sorts: all ScalarQuery (Q). ``BitAnd`` / ``BitOr`` / ``BitXor`` fold over
their children (identity ``-1`` for AND, ``0`` for OR / XOR); the shifts are
binary and ``BitNot`` is unary. Each atom defines ``compile`` (sync hot path)
and ``acompile`` (async hot path), both returning a thunk that captures the
precompiled child thunks. Sentinel propagation is inlined: an EMPTY or INVALID
operand collapses the result to INVALID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["BitAnd", "BitNot", "BitOr", "BitXor", "LShift", "RShift"]


class BitAnd(ScalarQuery):
    """The bitwise AND of its scalar children."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = -1
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out & v
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = -1
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out & v
            return out

        return athunk


class BitOr(ScalarQuery):
    """The bitwise OR of its scalar children."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = 0
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out | v
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = 0
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out | v
            return out

        return athunk


class BitXor(ScalarQuery):
    """The bitwise XOR of its scalar children."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            out: object = 0
            for ct in children:
                v = ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out ^ v
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            out: object = 0
            for ct in children:
                v = await ct(rt)
                if v is EMPTY or v is INVALID:
                    return INVALID
                out = out ^ v
            return out

        return athunk


class BitNot(ScalarQuery):
    """The bitwise NOT of its one child."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        def thunk(rt: Runtime) -> object:
            v = only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ~v

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (only,) = children

        async def athunk(rt: Runtime) -> object:
            v = await only(rt)
            if v is EMPTY or v is INVALID:
                return INVALID
            return ~v

        return athunk


class LShift(ScalarQuery):
    """The first child shifted left by the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a << b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a << b

        return athunk


class RShift(ScalarQuery):
    """The first child shifted right by the second."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        def thunk(rt: Runtime) -> object:
            a = left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >> b

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        left, right = children

        async def athunk(rt: Runtime) -> object:
            a = await left(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await right(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            return a >> b

        return athunk
