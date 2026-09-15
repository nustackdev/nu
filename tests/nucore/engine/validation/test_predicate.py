"""Unit tests for ``nu.engine.validation.predicate``.

Covers :class:`Predicate` and the ``@predicate`` decorator: the wrapper
contract, the algebra (``&``, ``|``, ``~``), the closure property of the
algebra, and the rules for mixing bare ``Test`` callables with predicates.
The tests pass ``None`` for ``program`` and ``path`` because no test below
actually reads from them -- the algebra is independent of the carrier.
"""

from __future__ import annotations

from nu.engine.validation import Predicate, predicate


# --- wrapper contract -----------------------------------------------------


def test_a_predicate_calls_through_to_its_underlying_test():
    p = Predicate(lambda program, path: True)
    assert p(None, None) is True


def test_decorator_preserves_function_name_and_docstring():
    @predicate
    def looks_like_a_leaf(program, path):
        """No children at this path."""
        return True

    assert looks_like_a_leaf.__name__ == "looks_like_a_leaf"
    assert looks_like_a_leaf.__doc__ == "No children at this path."


def test_repr_shows_the_wrapped_test_name():
    @predicate
    def my_test(program, path):
        return True

    assert repr(my_test) == "Predicate(my_test)"


# --- algebra: AND ---------------------------------------------------------


def test_and_returns_true_only_when_both_predicates_hold():
    truthy = Predicate(lambda program, path: True)
    falsy = Predicate(lambda program, path: False)
    assert (truthy & truthy)(None, None) is True
    assert (truthy & falsy)(None, None) is False
    assert (falsy & truthy)(None, None) is False


# --- algebra: OR ----------------------------------------------------------


def test_or_returns_true_when_either_predicate_holds():
    truthy = Predicate(lambda program, path: True)
    falsy = Predicate(lambda program, path: False)
    assert (truthy | falsy)(None, None) is True
    assert (falsy | truthy)(None, None) is True
    assert (falsy | falsy)(None, None) is False


# --- algebra: NOT ---------------------------------------------------------


def test_invert_flips_the_verdict():
    truthy = Predicate(lambda program, path: True)
    falsy = Predicate(lambda program, path: False)
    assert (~truthy)(None, None) is False
    assert (~falsy)(None, None) is True


# --- algebra closure ------------------------------------------------------


def test_combinators_return_predicate_instances():
    a = Predicate(lambda program, path: True)
    b = Predicate(lambda program, path: True)
    assert isinstance(a & b, Predicate)
    assert isinstance(a | b, Predicate)
    assert isinstance(~a, Predicate)


def test_bare_test_callable_on_the_right_of_a_combinator():
    truthy = Predicate(lambda program, path: True)

    def bare(program, path):
        return False

    assert (truthy & bare)(None, None) is False
    assert (truthy | bare)(None, None) is True


def test_chained_algebra_evaluates_as_expected():
    t = Predicate(lambda program, path: True)
    f = Predicate(lambda program, path: False)
    # (T & F) | ~F  ==  False | True  ==  True
    assert ((t & f) | ~f)(None, None) is True
    # (T | F) & ~T  ==  True & False  ==  False
    assert ((t | f) & ~t)(None, None) is False
