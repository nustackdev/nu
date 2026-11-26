"""The cluster ``Teleport`` ships its args with the body, without a real ray cluster.

A stand-in service is bound under ``RayService``: its ``aexecute`` puts the
term through the wire and runs it on a Context of its own, the way the actor
does, so nothing of the caller's Context reaches the body.
"""

from __future__ import annotations

import pytest

import nu
from nu.lang import wire
from nustd.cluster import Teleport
from nustd.cluster.resources import RayService


class _Service:
    """What the Teleport needs of a ``RayService``: ``aexecute(tree)``, run elsewhere."""

    def __init__(self) -> None:
        self.trees: list[object] = []

    async def aexecute(self, tree: object) -> object:
        self.trees.append(tree)
        value, _ = await nu.arun(wire.loads(wire.dumps(tree)), nu.Context())
        return value


def _ctx(service: _Service, *tags: object) -> nu.Context:
    return nu.Context().bind(RayService, service, *tags)  # type: ignore[arg-type]


async def test_args_cross_with_the_body():
    service = _Service()
    tree = nu.let(lambda seed: Teleport(lambda a, b: nu.Add(a, b), 0, a=seed * 2, b=1), seed=20)
    assert (await nu.arun(tree, _ctx(service, 0)))[0] == 41


async def test_a_tree_body_with_no_args():
    service = _Service()
    body = nu.Add(1, 2)
    assert (await nu.arun(Teleport(body), _ctx(service)))[0] == 3
    assert service.trees[0] is body


async def test_target_is_positional_so_a_parameter_can_take_its_name():
    service = _Service()
    tree = Teleport(lambda target, body: nu.Add(target, body), "main", target=1, body=2)
    assert (await nu.arun(tree, _ctx(service, "main")))[0] == 3


async def test_the_caller_context_does_not_cross():
    service = _Service()
    tree = nu.let(lambda outer: Teleport(nu.Add(outer, 1)), outer=1)
    with pytest.raises(LookupError):
        await nu.arun(tree, _ctx(service))


def test_args_are_checked_at_build():
    with pytest.raises(TypeError, match="no value for"):
        Teleport(lambda a: a)
    with pytest.raises(TypeError, match="a tree body takes no values"):
        Teleport(nu.Add(1, 2), a=1)
