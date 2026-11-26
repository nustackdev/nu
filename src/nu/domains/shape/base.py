"""The address chain every shape ref is: a parent on the tree, then its own address.

A ref's parent is ``children[0]`` (structural: walked, never value-read) and its
own address is ``children[1]`` (a value, resolved through the runtime like any
child). A chain's top ref points at the shared :data:`ANCHOR`, so every generic
pass reaches the whole chain as ordinary tree.

Substrates fill the plug-points here with their own storage walk; nothing in
this module knows how any fabric reads or writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from nu.engine import Declared
from nu.lang import NULL, Literal, Ref
from nu.lang.null import is_null


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.domains.shape.dsl import Shape
    from nu.lang.runtime import Runtime
    from nu.lang.typeinfo import TypeInfo

__all__ = ["ANCHOR", "Anchor", "StructuredRef", "root_shape"]


_R = TypeVar("_R")


class Anchor(Ref):
    """Terminates a StructuredRef parent chain at the fabric root.

    A structural leaf: no children, no address, ``structural`` empty (it is not
    a StructuredRef). It is never value-read: it only marks where a chain's
    parent walk bottoms out. Stateless, so one shared instance (:data:`ANCHOR`)
    backs every chain root.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return lambda rt: NULL

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return NULL

        return athunk


ANCHOR = Anchor()


class StructuredRef(Ref):
    """Abstract base for shape-fabric Refs.

    ``children[0]`` = parent (a StructuredRef, or :data:`ANCHOR` at a chain
    root), marked ``structural``. ``children[1]`` = this Ref's address (a value).
    """

    _structural = Declared(value=frozenset({0}), name="structural")

    def __init__(
        self,
        address: object,
        *,
        parent_ref: StructuredRef | None = None,
        owner_shape: type[Shape] | None = None,
        type_info: TypeInfo | None = None,
    ) -> None:
        parent = parent_ref if parent_ref is not None else ANCHOR
        super().__init__(parent, address)
        # Fields are underscore-named: a public attribute would shadow a slot of
        # the same name on the refs that navigate by ``__getattr__``.
        self._owner_shape: type[Shape] | None = owner_shape
        """Shape class that directly owns this slot."""
        self._type_info: TypeInfo | None = type_info
        """What the slot declared this ref holds; None when nothing is declared."""

    #: Set (via ``evolve``) on every spine node ``with_parent`` placed. A placed
    #: chain and a fresh one both bottom out at ANCHOR, so the mark is the only
    #: way to tell. A class default, so an unplaced ref carries no field for it.
    _placed: bool = False

    # --- navigation (all private: inner mechanics, never user-facing) ---------

    @property
    def _parent(self) -> StructuredRef | None:
        """Parent Ref in the navigation chain; None at a chain root (ANCHOR).

        Private: core navigation machinery, not user-facing. Underscore also keeps
        it clear of value-domain members like ``PurePath.parent`` that a typed leaf
        Ref exposes on its public surface.
        """
        p = self._children[0]
        return p if isinstance(p, StructuredRef) else None

    @property
    def _segment(self) -> object:
        """This ref's address as given: a Literal's value, else the address term.

        Read off ``children[1]``, so it is never stored twice. A computed
        address (a Ref, an expression) comes back as the term itself.

        Build time only: the ui key builders, ``same_place`` and messages read
        it to name a place. A run never reads it; it runs the address child
        (``_address``, the substrates' path walks).
        """
        address = self._children[1]
        if isinstance(address, Literal) and address.factory is None:
            return address.value
        return address

    @property
    def _root_shape(self) -> type[Shape] | None:
        """Root Shape for this Ref chain: the owner shape of the chain's top ref.

        Computed by walking ``children[0]`` up to :data:`ANCHOR`, so a chain
        spliced or placed under another ref routes to that ref's root with no
        bookkeeping.
        """
        node = self
        while isinstance(parent := node._children[0], StructuredRef):
            node = parent
        return node._owner_shape

    # --- declaration -----------------------------------------------------------

    @classmethod
    def _slot_kwargs_from_type_args(cls, args: tuple) -> dict[str, object]:
        """What a slot annotated ``RefClass[args]`` passes to its constructor.

        Nothing by default. A ref whose constructor needs one of the type
        arguments (``ShapeRef[Order]``) or checks them overrides this.
        """
        return {}

    # --- placement -------------------------------------------------------------

    def with_parent(self, parent: StructuredRef) -> StructuredRef:
        """This chain, its head placed under ``parent``, so its slots read typed there.

        ``Counter.value.with_parent(State.cells[cell_id])`` reads and writes
        ``State.cells[cell_id].value`` as an int, in ``State``'s store. Only the
        spine moves; a ref used as an index inside the chain stays as it is.
        The name is reserved: no Shape can declare a slot called
        ``with_parent``.

        Raises:
            TypeError: ``parent`` is not a shape ref.
            ValueError: this chain was already placed.
        """
        from .rewrite import with_parent

        return with_parent(self, parent)

    # --- re-kind ---------------------------------------------------------------

    # ``Kind.slot(...)`` is typed as the ref it builds (a ``Slot`` at run
    # time), so both forms resolve to the ref class.
    @overload
    def to(self, spec: type[_R]) -> _R: ...

    @overload
    def to(self, spec: _R) -> _R: ...

    def to(self, spec: type[_R] | _R) -> _R:
        """This address as the kind ``spec`` names, so the chain goes on in that kind.

        ``grid[0, 1].to(TableRef.slot(columns=cols))[1, 0]``. The
        kind is named where the child is used, never declared on the container,
        which is what lets one container hold children of different kinds.

        The result replaces this ref: same parent, same address, the class and
        props ``spec`` carries. Nothing of this ref's own kind comes along; its
        declared ``type_info`` belonged to the kind it had. Whether the store
        agrees with the new kind is the fabric's to check when it is used.

        Every shape ref has it, leaf or container, so a re-kinded ref re-kinds
        again: ``ref.to(DictRef).to(IntRef)`` is ``ref.to(IntRef)``. The name
        is reserved: no Shape can declare a slot called ``to``.

        Args:
            spec: a ref class (no props), or a slot spec ``Kind.slot(**props)``,
                which is also how a Shape-backed kind is named.

        Raises:
            TypeError: ``spec`` is neither a shape ref class nor a ``Slot``.
        """
        from .dsl import Slot

        if isinstance(spec, Slot):
            slot = spec
        elif isinstance(spec, type) and issubclass(spec, StructuredRef):
            slot = Slot(spec)
        else:
            msg = (
                f"{type(self).__name__}.to takes a ref class or a Kind.slot(...) spec, not {spec!r}"
            )
            raise TypeError(msg)
        # A plain key was wrapped in a Literal when this ref was built; hand the
        # new one the key itself, so it is built exactly as this one was.
        address = self._children[1]
        if type(address) is Literal and address.factory is None:
            address = address.value
        ref = slot.create_ref(
            owner_shape=self._owner_shape,
            parent_ref=self._parent,
            address=address,
        )
        # Same parent, so the root shape comes along on its own. A chain placed
        # by ``with_parent`` stays placed.
        if self._placed:
            ref = ref.evolve(_placed=True)
        return ref  # type: ignore[return-value]

    # --- address resolution --------------------------------------------------

    def _address(self, rt: Runtime, nid: int) -> object:
        """Resolve this Ref's own address (``children[1]``); nid is this node's id."""
        return rt.eval(rt.program.children[nid][1])

    async def _aaddress(self, rt: Runtime, nid: int) -> object:
        """Async sibling of :meth:`address`."""
        return await rt.aeval(rt.program.children[nid][1])

    # --- substrate plug-points (deferred) ------------------------------------

    async def _afetch_parent(self, rt: Runtime, nid: int) -> object:
        """Fetch the parent container holding this Ref's slot. Substrate-specific."""
        msg = f"{type(self).__name__}._afetch_parent is not implemented"
        raise NotImplementedError(msg)

    async def _aresolve_address(self, rt: Runtime, nid: int) -> object:
        """Resolve this segment's address against the runtime. Substrate-specific."""
        msg = f"{type(self).__name__}._aresolve_address is not implemented"
        raise NotImplementedError(msg)

    def _wrap_item_ref(self, address: object) -> StructuredRef:
        """Build the child Ref at ``address``, with self as parent. Substrate-specific.

        The one wrap hook that returns a ref rather than a form: which ref holds
        a container's declared value is the fabric's to say, so no blueprint
        builds one.
        """
        msg = f"{type(self).__name__}._wrap_item_ref is not implemented"
        raise NotImplementedError(msg)

    def _primitive_write(self, rt: Runtime, value: object, nid_self: int) -> None:
        """Write ``value`` as a single primitive blob, bypassing compound decomposition.

        Override in substrates that support primitive-blob storage
        (e.g. PrimitiveDictRef, PrimitiveListRef, PrimitiveSetRef).
        Called by ``PrimitiveSet``.
        """
        msg = f"{type(self).__name__}._primitive_write is not implemented"
        raise NotImplementedError(msg)

    async def _aprimitive_write(self, rt: Runtime, value: object, nid_self: int) -> None:
        """Async sibling of :meth:`_primitive_write`."""
        msg = f"{type(self).__name__}._aprimitive_write is not implemented"
        raise NotImplementedError(msg)

    def _exists(self, rt: Runtime, nid: int) -> bool:
        """Whether this Ref's address holds a value; nid is this node's id.

        By default its read is not NULL. A substrate whose read never is NULL
        (a lazy container handle) overrides this. Called by ``Exists``.
        """
        return not is_null(rt.eval(nid))

    async def _aexists(self, rt: Runtime, nid: int) -> bool:
        """Async sibling of :meth:`_exists`."""
        return not is_null(await rt.aeval(nid))

    # --- value boundary: lift (storage -> domain) / lower (domain -> storage) -

    def _lift(self, raw: object) -> object:
        """Raw storage value -> typed domain value.

        Identity by default; substrates override when the storage representation
        differs from the domain type (e.g. ISO string -> datetime). Guaranteed on
        EVERY read path.
        """
        return raw

    async def _alift(self, raw: object) -> object:
        """Async sibling of :meth:`_lift`; reuses the sync form by default.

        Lifting is pure storage->domain shaping, so a ref overriding only
        ``_lift`` is correct on both read paths; override this too only for
        genuinely async lifting.
        """
        return self._lift(raw)

    def _lower(self, value: object) -> object:
        """Typed domain value -> storage form. The inverse of :meth:`_lift`.

        Identity by default; applied on every write path so ``store``/``write``
        take one canonical typed input.
        """
        return value

    async def _alower(self, value: object) -> object:
        """Async sibling of :meth:`_lower`; reuses the sync form by default."""
        return self._lower(value)


def root_shape(ref: StructuredRef) -> type[Shape] | None:
    """The Shape class a Ref chain is rooted at.

    A chain finds its fabric by this class: which Navigator answers it, which
    transaction it writes through, which shard it lives on. So anything handed
    a Ref as a *location* and then building its own reads underneath it has to
    carry the class along, or the reads land on whatever is bound untagged.

    A function rather than a property because a Ref's attribute surface belongs
    to the value it names: every public name there is a name a Shape can no
    longer use for a slot.

    Returns:
        None for a chain nothing owns -- a Ref built outside a Shape class.
    """
    return ref._root_shape
