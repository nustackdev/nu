// Tabs -- tab strip plus active body.
//
// Pairing: the old module took a `children` path list and lined it up with
// `tabs[i]` by index. Tree children keep exactly that rule -- `useChildren`
// gives the segments in insertion order (order of first write) and child `i`
// is the body of `tabs[i]`. So the server still has to write the bodies in
// tab order; nothing keys a body to a tab id. We render each body ourselves
// instead of via `NodeChildren` because every one has to sit in its own
// `TabsContent` panel.
//
// Server-owned tabs / active (with optimistic local active on click). Two
// inbound ops the default `write` cannot express:
//   set_tabs   replace the tabs list wholesale
//   set_active set the active tab id (server pin / confirmation)
// One outbound notify on user click: payload is the clicked tab id. The
// server may mirror it back via set_active. Inactive bodies stay mounted
// (via forceMount + `hidden`) so leaf components keep their local state.
// Composes the kit Tabs primitive family (Radix Tabs under the hood).

import { OPS } from "@nustackdev/ui-core";
import {
	TabsContent,
	TabsList,
	Tabs as TabsPrimitive,
	TabsTrigger,
} from "../../components/ui/tabs";
import {
	type NodeEntry,
	type NodeProps,
	NodeView,
	useChildren,
	useListProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

type Tab = { id: string; label: string };

function normalizeTabs(raw: unknown): Tab[] {
	if (!Array.isArray(raw)) return [];
	const out: Tab[] = [];
	for (const item of raw) {
		if (!item || typeof item !== "object") continue;
		const o = item as { id?: unknown; label?: unknown };
		if (o.id == null) continue;
		const id = String(o.id);
		const label = o.label == null ? "" : String(o.label);
		out.push({ id, label });
	}
	return out;
}

function TabsView({ path }: NodeProps) {
	const rawTabs = useListProp<unknown>(path, "tabs");
	const active = useStringProp(path, "active");
	const children = useChildren(path);
	const setProps = useSetProps(path);
	const send = useSend(path);

	const tabs = normalizeTabs(rawTabs);
	const activeId = active && tabs.some((t) => t.id === active) ? active : (tabs[0]?.id ?? "");
	const n = Math.min(tabs.length, children.length);

	const onValueChange = (next: string) => {
		// optimistic: pin locally first, then tell the server.
		setProps({ active: next });
		send(OPS.notify, next);
	};

	if (n === 0) return null;

	return (
		<TabsPrimitive value={activeId} onValueChange={onValueChange}>
			<TabsList variant="line">
				{tabs.slice(0, n).map((t) => (
					<TabsTrigger key={t.id} value={t.id} variant="line">
						{t.label}
					</TabsTrigger>
				))}
			</TabsList>
			{Array.from({ length: n }).map((_, i) => {
				const segment = children[i];
				const tab = tabs[i];
				return (
					<TabsContent
						// forceMount keeps inactive bodies rendered so leaf component
						// state survives across tab switches; Radix hides the panel via
						// `data-state="inactive"` when it is not the current tab.
						forceMount
						key={segment}
						value={tab.id}
						hidden={tab.id !== activeId}
					>
						<NodeView path={[...path, segment]} />
					</TabsContent>
				);
			})}
		</TabsPrimitive>
	);
}

export const Tabs: NodeEntry = {
	component: TabsView,
	handlers: {
		set_tabs: (ctx, payload) =>
			ctx.update((props) => {
				props.tabs = normalizeTabs(payload);
			}),
		set_active: (ctx, payload) =>
			ctx.update((props) => {
				props.active = payload == null ? "" : String(payload);
			}),
	},
};
