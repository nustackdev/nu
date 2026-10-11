// ListRef -- a bulleted or numbered list whose items are any nodes.
//
// A container. Plain string items come first: they live on the node as
// `items: string[]`, one string per item, drawn as given. Then every child
// node is one more item after them, each in its own `ListItem`, in insertion
// order, so numbering runs on from the strings. There is no item type: any
// child is an item. Children see a block flow, the same as in a Column.
//
// Composes the kit List primitive. Its box carries the same 4px of vertical
// padding as every text output (see TextRef, Prose), padding and never
// margin.
//
// Wire (the strings only; children arrive as their own nodes):
//   write   a list replaces the items wholesale, each one stringified; a map
//           merges {items, variant, start} like every other node; nil clears.
//   append  push one item to the end.

import { List, ListItem, type ListVariant } from "../../components/ui/list";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useListProp,
	useProp,
	useStringProp,
} from "../../tree";

const VARIANTS = new Set<ListVariant>(["bullet", "number"]);

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
	const variant = useStringProp(path, "variant", "bullet") as ListVariant;
	const rawStart = useProp<unknown>(path, "start", 1);
	const start = typeof rawStart === "number" ? rawStart : 1;
	return (
		<List variant={VARIANTS.has(variant) ? variant : "bullet"} start={start} className="py-1">
			{normalizeItems(items).map((item, i) => (
				// Items are plain strings with no id of their own; position is the identity.
				// biome-ignore lint/suspicious/noArrayIndexKey: see above
				<ListItem key={i}>{item}</ListItem>
			))}
			<FlowProvider flow="block">
				<NodeChildren path={path} cell={ItemCell} />
			</FlowProvider>
		</List>
	);
}

export const ListRef: NodeEntry = {
	component: ListView,
	fill: true,
	handlers: {
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
