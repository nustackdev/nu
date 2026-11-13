// The browser store, as a tree.
//
// One node is three things: a `type`, a bag of `props`, and `children`
// keyed by segment (plus the `hidden` flag the visibility ops set). `type` is
// null for a node that exists only because something below it was written.
// `value` is just a prop, not a field of its own -- a node's current value
// lives at `props.value` like everything else.
//
// Writes autovivify. A frame carries a `chain`, root-first, one triple per
// level, so a write to `a.b.c` creates `a` and `b` with the type and props
// each was annotated with, exactly like a kv set on a nested path. Nothing is
// mounted ahead of time and there is no fields list. Chain props are a seed
// for a level being created, never an update to one already there.
//
// A node's type is fixed once named. A chain that names another type for a
// node already there is refused whole: nothing lands, `onError` reports it and
// a frame from the server gets an `error` frame back. Changing what sits at an
// address takes a `remove` first.
//
// React-free on purpose: this is zustand's vanilla store, so core stays usable
// from a worker, a test, or anywhere else with no DOM. The React bindings and
// the component registry live in the kit.

import { current, enableMapSet, isDraft } from "immer";
import { immer } from "zustand/middleware/immer";
import { createStore, type StoreApi } from "zustand/vanilla";
import { type ChainLevel, type ErrorPayload, type Frame, OP_ERROR } from "./protocol";

// `children` is a Map, and immer only drafts those once this is on.
enableMapSet();

/** A node's address: segments, root-first. A segment may contain any character. */
export type Path = string[];

export type Props = Record<string, unknown>;

// A Map and not a plain object: render order is insertion order, and an
// object hoists integer-like keys to the front, so a segment like "0" or an
// index from a dynamic ref would silently jump the queue.
//
// `hidden` lives on the node and not in its props, so no prop merge and no
// type's own write handler can clobber it. Unset means shown.
export type Node = {
	type: string | null;
	props: Props;
	children: Map<string, Node>;
	hidden?: boolean;
	// The props the node's slot declared, as they came on the chain that
	// created it. Never written after that, so a reset (an input back to its
	// declared value) has something to go back to once the live props moved.
	seed?: Props;
};

/** Alias for consumers where the DOM's `Node` is also in scope. */
export type TreeNode = Node;

// One level of a write's chain: the segment, the type the level should have,
// and the props its slot declared. This is the wire `ChainLevel`: a frame
// that arrives with no chain gets one synthesized from its ref, and those
// levels know neither type nor props.
//
// Chain props are a create-time seed and nothing else. The same chain rides
// along on every write to anything below that level, carrying the declared
// defaults, so merging them into a level that already exists would stomp on
// whatever the program set at runtime. An existing level is compared by type
// and otherwise left alone.
export type ChainStep = ChainLevel;

// A frame as it arrives. The chain is the wire type, so this is `Frame`; the
// alias stays because the store talks about frames it may have synthesized.
export type TreeFrame = Frame;

/** The op vocabulary. There is no mount and no unmount. */
export const OPS = {
	write: "write",
	// Chain only, no payload: brings a node into being ahead of the first
	// write to it. What a boot batch is made of.
	init: "init",
	remove: "remove",
	// Chain only, no payload, like init. Hide keeps the node, its props and
	// its children (state survives, the browser just draws nothing); display
	// shows it again. Every type takes them, none handles them.
	hide: "hide",
	display: "display",
	read: "read",
	notify: "notify",
} as const;

export type NodeCtx = {
	path: Path;
	/** Snapshot of the node at dispatch time. */
	node: Node;
	/** Mutate this node's own props. */
	update: (mutate: (props: Props) => void) => void;
	/** Send a frame rooted at this node. */
	send: (op: string, payload: unknown, id?: string) => void;
	store: TreeStore;
	frame: TreeFrame;
};

export type NodeHandler = (ctx: NodeCtx, payload: unknown) => void;

export type DisposeCtx = { path: Path; node: Node };

/** What a type contributes to the store: inbound ops and teardown. */
export type Behaviour = {
	handlers?: Record<string, NodeHandler>;
	dispose?: (ctx: DisposeCtx) => void;
};

export type Resolve = (type: string) => Behaviour | undefined;

export type TreeState = { root: Node };

export type TreeActions = {
	/**
	 * Walk the chain, creating what is missing, then merge `props` into the leaf.
	 * False when the chain names a kind other than a node's already there: the
	 * write is refused whole and `onError` has it.
	 */
	write: (chain: ChainStep[], props?: Props) => boolean;
	/** Drop a subtree, running dispose down the branch. Server-driven only. */
	remove: (path: Path) => void;
	getIn: (path: Path) => Node | null;
	/** Merge props into an existing node. No-op when the node is not there. */
	setProps: (path: Path, props: Props) => void;
	/** Hide or show an existing node. No-op when the node is not there. */
	setHidden: (path: Path, hidden: boolean) => void;
	/** Route an inbound frame to its node, by node type and frame op. */
	dispatch: (frame: TreeFrame) => void;
	/** Outbound. No-op until a sender is set. */
	send: (frame: TreeFrame) => void;
	setSender: (send: ((frame: TreeFrame) => void) | null) => void;
	setResolve: (resolve: Resolve) => void;
};

export type TreeStore = StoreApi<TreeState & TreeActions>;

export type TreeStoreOptions = {
	/** Behaviour lookup by type name. The kit registry supplies this. */
	resolve?: Resolve;
	send?: (frame: TreeFrame) => void;
	onError?: (message: string, path: Path) => void;
};

export function emptyNode(type: string | null = null): Node {
	return { type, props: {}, children: new Map() };
}

function isPlainProps(v: unknown): v is Props {
	return typeof v === "object" && v !== null && !Array.isArray(v);
}

/** A write payload as props: an object merges, anything else lands on `value`. */
export function asProps(payload: unknown): Props {
	return isPlainProps(payload) ? payload : { value: payload };
}

/** The chain a frame carries, or an untyped one built from its ref. */
export function frameChain(frame: TreeFrame): ChainStep[] {
	if (frame.chain) return frame.chain;
	return frame.ref.map((segment) => [segment, null] as ChainStep);
}

/** Where `chain` names a type other than the node already there has, or null. */
export function kindConflict(
	root: Node,
	chain: ChainStep[],
): { path: Path; have: string; want: string } | null {
	let node: Node = root;
	const here: Path = [];
	for (const [segment, rawType] of chain) {
		const child = node.children.get(segment);
		if (!child) return null;
		here.push(segment);
		const want = rawType ?? null;
		// An untyped side on either end is no claim: a synthesized chain names
		// no type, and an autovivified level takes the first one named.
		if (want !== null && child.type !== null && child.type !== want) {
			return { path: [...here], have: child.type, want };
		}
		node = child;
	}
	return null;
}

function mismatch(conflict: { path: Path; have: string; want: string }): string {
	return (
		`kind mismatch at ${conflict.path.join(" / ")}: the node is ${conflict.have}, ` +
		`the write names ${conflict.want}; remove it first to put another kind there`
	);
}

/** Pure lookup, handy for selectors over a state snapshot. */
export function getNode(root: Node, path: Path): Node | null {
	let node: Node = root;
	for (const segment of path) {
		const next = node.children.get(segment);
		if (!next) return null;
		node = next;
	}
	return node;
}

// Post-order: a child tears down before its parent. The node is snapshotted
// out of the draft first -- disposals run after the set returns, by which
// point a draft proxy is dead.
function collectDispose(draftNode: Node, path: Path, out: DisposeCtx[]): void {
	walkDispose(isDraft(draftNode) ? (current(draftNode) as Node) : draftNode, path, out);
}

function walkDispose(node: Node, path: Path, out: DisposeCtx[]): void {
	for (const [segment, child] of node.children) {
		walkDispose(child, [...path, segment], out);
	}
	if (node.type !== null) out.push({ path, node });
}

export function createTreeStore(options: TreeStoreOptions = {}): TreeStore {
	let resolve: Resolve = options.resolve ?? (() => undefined);
	let outbound = options.send ?? null;
	const onError =
		options.onError ??
		((message: string, path: Path) => console.error(`nu.ui [${path.join(" / ")}]: ${message}`));

	// Disposals are collected inside a draft and run after the set returns, so
	// a dispose is free to touch the store without writing into a dead draft.
	let pending: DisposeCtx[] = [];
	const flushDispose = () => {
		const batch = pending;
		pending = [];
		for (const ctx of batch) {
			const behaviour = ctx.node.type ? resolve(ctx.node.type) : undefined;
			if (!behaviour?.dispose) continue;
			try {
				behaviour.dispose(ctx);
			} catch (err) {
				console.warn(`nu.ui: dispose threw for ${ctx.path.join(" / ")}`, err);
			}
		}
	};

	const store: TreeStore = createStore<TreeState & TreeActions>()(
		immer((set, get) => ({
			root: emptyNode(),

			write: (chain, props) => {
				const path = chain.map((step) => step[0]);
				const conflict = kindConflict(get().root, chain);
				if (conflict) {
					onError(mismatch(conflict), path);
					return false;
				}
				// When the leaf is already there, the conflict walk has seen every
				// level above it agree, so only the payload lands.
				const existing = getNode(get().root, path);
				if (existing) {
					const leafType = chain.length ? (chain[chain.length - 1][1] ?? null) : null;
					if (leafType === null || existing.type !== null) {
						if (props && Object.keys(props).length) get().setProps(path, props);
						return true;
					}
				}
				set((draft) => {
					let node = draft.root as Node;
					const here: Path = [];
					for (const [segment, rawType, stepProps] of chain) {
						here.push(segment);
						const type = rawType ?? null;
						let child: Node | undefined = node.children.get(segment);
						if (!child) {
							child = emptyNode(type);
							if (stepProps) {
								Object.assign(child.props, stepProps);
								child.seed = { ...stepProps };
							}
							node.children.set(segment, child);
						} else if (child.type === null && type !== null) {
							// Autovivified earlier by something below it, so it
							// never got its declared props. This write names its
							// type, which is when it really comes into being.
							child.type = type;
							if (stepProps) {
								Object.assign(child.props, stepProps);
								child.seed = { ...stepProps };
							}
						}
						// Otherwise: the level is already there with the right
						// type. The chain says nothing new about it.
						node = child;
					}
					if (props) Object.assign(node.props, props);
				});
				return true;
			},

			remove: (path) => {
				if (!path.length) {
					set((draft) => {
						collectDispose(draft.root as Node, [], pending);
						draft.root = emptyNode();
					});
					flushDispose();
					return;
				}
				const parentPath = path.slice(0, -1);
				const segment = path[path.length - 1];
				set((draft) => {
					const parent = getNode(draft.root as Node, parentPath);
					const node = parent?.children.get(segment);
					if (!parent || !node) return;
					collectDispose(node, path, pending);
					parent.children.delete(segment);
				});
				flushDispose();
			},

			getIn: (path) => getNode(get().root, path),

			setProps: (path, props) =>
				set((draft) => {
					const node = getNode(draft.root as Node, path);
					if (!node) return;
					Object.assign(node.props, props);
				}),

			setHidden: (path, hidden) => {
				const node = getNode(get().root, path);
				if (!node || Boolean(node.hidden) === hidden) return;
				set((draft) => {
					const target = getNode(draft.root as Node, path);
					if (!target) return;
					if (hidden) target.hidden = true;
					else delete target.hidden;
				});
			},

			send: (frame) => {
				if (outbound) outbound(frame);
			},

			setSender: (sender) => {
				outbound = sender;
			},

			setResolve: (next) => {
				resolve = next;
			},

			dispatch: (frame) => {
				const api = get();
				if (frame.op === OP_ERROR) {
					const payload = (frame.payload ?? {}) as Partial<ErrorPayload>;
					onError(`server: ${payload.message ?? payload.code ?? "error"}`, frame.ref);
					return;
				}
				// A chain the store refused never reaches a handler; the server
				// hears why, since the write it sent did not land.
				const refuse = () => {
					const conflict = kindConflict(api.root, frameChain(frame));
					const message = conflict ? mismatch(conflict) : "write refused";
					api.send({
						op: OP_ERROR,
						ref: frame.ref,
						payload: { code: "kind_mismatch", message } satisfies ErrorPayload,
						id: frame.id,
					});
				};
				if (frame.op === OPS.remove) {
					api.remove(frame.ref);
					return;
				}
				const chain = frameChain(frame);
				if (frame.op === OPS.init) {
					// Structure and nothing else. An init carries no payload, so
					// it never touches a value the program already set.
					if (!api.write(chain)) refuse();
					return;
				}
				if (frame.op === OPS.hide || frame.op === OPS.display) {
					// Structure first (the node may not exist yet), then the
					// flag. Generic for every type, never a handler's call.
					if (!api.write(chain)) {
						refuse();
						return;
					}
					api.setHidden(frame.ref, frame.op === OPS.hide);
					return;
				}
				const handlerFor = (node: Node | null) => {
					const behaviour = node?.type ? resolve(node.type) : undefined;
					return behaviour?.handlers?.[frame.op];
				};
				if (frame.op === OPS.write) {
					// Structure first, always: the node may not exist yet, so
					// the chain runs before anything can be looked up by type.
					if (!api.write(chain)) {
						refuse();
						return;
					}
					const written = api.getIn(frame.ref);
					if (!written) return;
					const custom = handlerFor(written);
					if (custom) {
						// The type owns what its payload means.
						custom(makeCtx(store, frame, written), frame.payload);
						return;
					}
					if (frame.payload !== undefined) {
						api.setProps(frame.ref, asProps(frame.payload));
					}
					return;
				}
				// Any other op that carries a chain brings its node into being
				// first, the same way a write does: a Card's `set_title` may be
				// the first frame that ever names that Card. A frame with no
				// chain is addressed at a node that should already be there.
				if (frame.chain && !api.write(chain)) {
					refuse();
					return;
				}
				const node = api.getIn(frame.ref);
				if (!node) {
					onError(`no node for op "${frame.op}"`, frame.ref);
					return;
				}
				const handler = handlerFor(node);
				if (handler) {
					handler(makeCtx(store, frame, node), frame.payload);
					return;
				}
				if (frame.op === OPS.read) {
					// The server is asking for our current value. Same id back
					// so its future resolves.
					api.send({
						op: OPS.read,
						ref: frame.ref,
						payload: node.props.value ?? null,
						id: frame.id,
					});
					return;
				}
				onError(`op "${frame.op}" not supported by ${node.type ?? "untyped node"}`, frame.ref);
			},
		})),
	);

	return store;
}

function makeCtx(store: TreeStore, frame: TreeFrame, node: Node): NodeCtx {
	const path = frame.ref;
	return {
		path,
		node,
		frame,
		store,
		update: (mutate) => {
			const current = store.getState().getIn(path);
			const next: Props = { ...(current?.props ?? node.props) };
			mutate(next);
			store.getState().setProps(path, next);
		},
		send: (op, payload, id) => store.getState().send({ op, ref: path, payload, id }),
	};
}
