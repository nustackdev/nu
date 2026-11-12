// Keyed order: where the children of an ordered collection draw.
//
// A child's segment is its key, its identity; where it draws is a place in
// the collection's order. The order is the collection's own prop
// (`props.order`, a list of segments) and the browser is the only one that
// holds it: the server never knows which children are there, so each op
// names keys and positions and the store works out the rest here.
//
// - No order yet: children draw in the default order, `indexedOrder`
//   (index segments by number, named ones where first written).
// - The first op writes the order down as drawn, every child placed. From
//   then on a child with no place (written after) draws after the placed
//   ones, in the default order among themselves.
// - A place may hold no child: `insert` before the child is written, or a
//   child erased on its own (`remove` on its path). A child written there
//   later shows in that place. Places with no child draw nothing.
// - insert / move edit one place and rewrite no child. remove / truncate /
//   keep drop children and their places together.
//
// Ops (payload, keys as segment text):
//   insert_item     {key, at? | before? | after?}  none of them: the end
//   move_item       {key, at? | before? | after?}  the key must be there
//   remove_item     {key}                           missing key: no-op
//   truncate_items  {count}                         keep the first count places
//   keep_items      {keys}                          drop every other child
//   order_items     {keys}                          these first, the rest after

import { OP_ERROR } from "./protocol";
import type { NodeCtx, NodeHandler, Path } from "./tree";

/** The prop an ordered collection keeps its order in. */
export const ORDER_PROP = "order";

/** The child ops of an ordered collection, by wire name. */
export const ORDER_OPS = {
	insert: "insert_item",
	move: "move_item",
	remove: "remove_item",
	truncate: "truncate_items",
	keep: "keep_items",
	order: "order_items",
} as const;

const isIndex = (s: string) => /^\d+$/.test(s);

/**
 * The default order: segments that are indices ("0", "1", ...) sort by
 * number among the places indexed children hold; named segments keep their
 * place in write order. So `[2]` written before `[0]` still draws 0 before 2.
 */
export function indexedOrder(segments: readonly string[]): string[] {
	const indexed = segments.filter(isIndex).sort((a, b) => Number(a) - Number(b));
	let next = 0;
	return segments.map((s) => (isIndex(s) ? indexed[next++] : s));
}

/** `raw` as an order, or undefined when it is not a list (no order kept yet). */
export function asOrder(raw: unknown): string[] | undefined {
	if (!Array.isArray(raw)) return undefined;
	return raw.map(String);
}

/**
 * Every place, in order: the kept order (empty places included), then each
 * child that has no place, in the default order. With no order kept yet,
 * just the default order.
 */
export function places(order: readonly string[] | undefined, present: readonly string[]): string[] {
	if (!order) return indexedOrder(present);
	const placed = new Set(order);
	return [...order, ...indexedOrder(present.filter((s) => !placed.has(s)))];
}

/** The order children draw in: every place that holds one of `present`. */
export function keyedOrder(
	order: readonly string[] | undefined,
	present: readonly string[],
): string[] {
	if (!order) return indexedOrder(present);
	const here = new Set(present);
	return places(order, present).filter((s) => here.has(s));
}

/** What an op does: the order to keep, and the children to drop. */
export type OrderEdit = { order: string[]; drop: string[] };

/** Why an op could not apply: the frame is refused and nothing changes. */
export class OrderError extends Error {}

type Payload = Record<string, unknown>;

function keyOf(payload: Payload, field = "key"): string {
	const raw = payload[field];
	if (typeof raw === "string" && raw) return raw;
	if (typeof raw === "number" && Number.isInteger(raw) && raw >= 0) return String(raw);
	throw new OrderError(`${field} must be a key, got ${JSON.stringify(raw)}`);
}

function keysOf(payload: Payload): string[] {
	const raw = payload.keys;
	if (!Array.isArray(raw)) throw new OrderError(`keys must be a list, got ${JSON.stringify(raw)}`);
	return raw.map(String);
}

// Where `key` goes in `rest` (the places without it): an index into `rest`.
function slotIn(rest: string[], payload: Payload): number {
	if (payload.at != null) {
		const at = Number(payload.at);
		if (!Number.isInteger(at) || at < 0) {
			throw new OrderError(`at must be a position >= 0, got ${JSON.stringify(payload.at)}`);
		}
		return Math.min(at, rest.length);
	}
	for (const side of ["before", "after"] as const) {
		if (payload[side] == null) continue;
		const anchor = keyOf(payload, side);
		const i = rest.indexOf(anchor);
		if (i < 0) throw new OrderError(`${side} names ${anchor}, which has no place here`);
		return side === "before" ? i : i + 1;
	}
	return rest.length;
}

function place(all: string[], key: string, payload: Payload): string[] {
	const rest = all.filter((s) => s !== key);
	const at = slotIn(rest, payload);
	return [...rest.slice(0, at), key, ...rest.slice(at)];
}

/**
 * Apply one op to an order. `order` is the kept one (undefined before the
 * first op), `present` the segments of the children there. Throws
 * `OrderError` for a payload it cannot apply; returns null for an op that
 * is not one of `ORDER_OPS`.
 */
export function applyOrderOp(
	op: string,
	rawPayload: unknown,
	order: readonly string[] | undefined,
	present: readonly string[],
): OrderEdit | null {
	const payload: Payload =
		typeof rawPayload === "object" && rawPayload !== null && !Array.isArray(rawPayload)
			? (rawPayload as Payload)
			: {};
	const all = places(order, present);
	const here = new Set(present);
	switch (op) {
		case ORDER_OPS.insert:
			return { order: place(all, keyOf(payload), payload), drop: [] };
		case ORDER_OPS.move: {
			const key = keyOf(payload);
			if (!all.includes(key)) throw new OrderError(`no child at ${key} to move`);
			return { order: place(all, key, payload), drop: [] };
		}
		case ORDER_OPS.remove: {
			const key = keyOf(payload);
			return { order: all.filter((s) => s !== key), drop: here.has(key) ? [key] : [] };
		}
		case ORDER_OPS.truncate: {
			const count = Number(payload.count);
			if (!Number.isInteger(count) || count < 0) {
				throw new OrderError(`count must be >= 0, got ${JSON.stringify(payload.count)}`);
			}
			const gone = all.slice(count);
			return { order: all.slice(0, count), drop: gone.filter((s) => here.has(s)) };
		}
		case ORDER_OPS.keep: {
			const kept = new Set(keysOf(payload));
			return {
				order: all.filter((s) => kept.has(s)),
				drop: all.filter((s) => !kept.has(s) && here.has(s)),
			};
		}
		case ORDER_OPS.order: {
			const first = [...new Set(keysOf(payload))].filter((s) => all.includes(s));
			const named = new Set(first);
			return { order: [...first, ...all.filter((s) => !named.has(s))], drop: [] };
		}
		default:
			return null;
	}
}

/**
 * Handlers that make a type an ordered collection: one per op in
 * `ORDER_OPS`, keeping the order in `props.order` and dropping children
 * through the store (so their dispose runs). A payload that cannot apply
 * changes nothing and goes back to the server as a `payload_invalid` error.
 */
export const orderHandlers: Record<string, NodeHandler> = Object.fromEntries(
	Object.values(ORDER_OPS).map((op) => [
		op,
		(ctx: NodeCtx, payload: unknown) => applyTo(ctx, op, payload),
	]),
);

function applyTo(ctx: NodeCtx, op: string, payload: unknown): void {
	const api = ctx.store.getState();
	const node = api.getIn(ctx.path) ?? ctx.node;
	let edit: OrderEdit | null;
	try {
		edit = applyOrderOp(op, payload, asOrder(node.props[ORDER_PROP]), [...node.children.keys()]);
	} catch (err) {
		if (!(err instanceof OrderError)) throw err;
		api.send({
			op: OP_ERROR,
			ref: ctx.path,
			payload: { code: "payload_invalid", message: `${op}: ${err.message}` },
			id: ctx.frame.id,
		});
		return;
	}
	if (!edit) return;
	const { order, drop } = edit;
	ctx.update((props) => {
		props[ORDER_PROP] = order;
	});
	for (const segment of drop) api.remove([...ctx.path, segment] as Path);
}
