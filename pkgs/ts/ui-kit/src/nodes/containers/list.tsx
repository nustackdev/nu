// ListRef -- a bulleted or numbered list whose items are any nodes.
//
// A container. Plain string items come first: they live on the node as
// `items: string[]`, one string per item, drawn as given. Then every child
// node is one more item after them, each in its own `ListItem`, so numbering
// runs on from the strings. Indexed children (`list[0]`, `list[1]` on the
// server) draw in index order whatever order they were written in; named
// ones keep their place in write order. There is no item type: any
// child is an item. Children see a block flow, the same as in a Column.
//
// Composes the kit List primitive. Its box carries the same 4px of vertical
// padding as every text output (see TextRef, Prose), padding and never
// margin.
//
// The children are a keyed, ordered collection. A child's segment is its
// key; where it draws is its place in the order the node keeps in
// `props.order` (ui-core `order.ts`). Until an order op arrives there is no
// kept order and children draw in index order as above; the first op writes
// the drawn order down, and from then on a child with no place draws after
// the placed ones. The string items always draw first.
//
// Wire (the strings; children arrive as their own nodes):
//   write   a list replaces the items wholesale, each one stringified; a map
//           merges {items, variant, start} like every other node; nil clears.
//   append  push one item to the end.
// Wire (the child order, see ui-core `ORDER_OPS`):
//   insert_item, move_item, remove_item, truncate_items, keep_items, order_items

import { asOrder, ORDER_PROP, orderHandlers } from "@nustackdev/ui-core";
import { List, ListItem, type ListVariant } from "../../components/ui/list";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useEnumProp,
	useListProp,
	useProp,
} from "../../tree";

const VARIANTS: readonly ListVariant[] = ["bullet", "number"];

function normalizeItems(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	return raw.filter((item) => item != null).map(String);
}

// One child node, one item.
function ItemCell({ children }: CellProps) {
	return <ListItem>{children}</ListItem>;
}

function ListView({ path }: NodeProps) {
	const items = useListProp<unknown>(path, "items");
	const variant = useEnumProp(path, "variant", VARIANTS, "bullet");
	const rawStart = useProp<unknown>(path, "start", 1);
	const start = typeof rawStart === "number" ? rawStart : 1;
	const order = asOrder(useProp<unknown>(path, ORDER_PROP, undefined));
	return (
		<List variant={variant} start={start} className="py-1">
			{normalizeItems(items).map((item, i) => (
				// Items are plain strings with no id of their own; position is the identity.
				// biome-ignore lint/suspicious/noArrayIndexKey: see above
				<ListItem key={i}>{item}</ListItem>
			))}
			<FlowProvider flow="block">
				<NodeChildren path={path} cell={ItemCell} indexed order={order} />
			</FlowProvider>
		</List>
	);
}

export const ListRef: NodeEntry = {
	component: ListView,
	fill: true,
	handlers: {
		...orderHandlers,
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null) {
					props.items = [];
					return;
				}
				if (Array.isArray(payload)) {
					props.items = normalizeItems(payload);
					return;
				}
				if (typeof payload === "object") {
					Object.assign(props, payload);
					if ("items" in payload) props.items = normalizeItems(props.items);
				}
			}),
		append: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null) return;
				props.items = [...normalizeItems(props.items), String(payload)];
			}),
	},
};
