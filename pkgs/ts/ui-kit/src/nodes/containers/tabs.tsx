// Tabs -- tab strip plus active body.
//
// Pairing: a tab's body is the child whose segment is the tab's id, so
// `tabs["overview"]` on the server is the overview panel whatever order the
// bodies were written in, and reordering the tabs list moves the bodies with
// it. A tab with no such child shows an empty panel; a child no tab names is
// not drawn. We render each body ourselves instead of via `NodeChildren`
// because every one has to sit in its own `TabsContent` panel.
//
// Server-owned tabs / active (with optimistic local active on click). Two
// inbound ops the default `write` cannot express:
//   set_tabs   replace the tabs list wholesale
//   set_active set the active tab id (server pin / confirmation)
// One outbound notify on user click: payload is the clicked tab id. The
// server may mirror it back via set_active. Inactive bodies stay mounted
// (via forceMount + `hidden`) so leaf components keep their local state.
// Composes the kit Tabs primitive family (Radix Tabs under the hood).
// `variant` is the strip's look, a plain prop the default `write` merges:
// `line` (underline, the default), `pill` (a wash chip behind the active
// tab) or `segmented` (one sunken track with a raised thumb). An unknown
// value reads as `line`.

import { OPS } from "@nustackdev/ui-core";
import {
	TabsContent,
	TabsList,
	Tabs as TabsPrimitive,
	TabsTrigger,
} from "../../components/ui/tabs";
import {
	FlowProvider,
	type NodeEntry,
	type NodeProps,
	NodeView,
	useChildren,
	useEnumProp,
	useListProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

type Tab = { id: string; label: string };
const VARIANTS = ["line", "pill", "segmented"] as const;

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
	const variant = useEnumProp(path, "variant", VARIANTS, "line");
	const children = useChildren(path);
	const setProps = useSetProps(path);
	const send = useSend(path);

	const tabs = normalizeTabs(rawTabs);
	const activeId = active && tabs.some((t) => t.id === active) ? active : (tabs[0]?.id ?? "");
	const bodies = new Set(children);

	const onValueChange = (next: string) => {
		// optimistic: pin locally first, then tell the server.
		setProps({ active: next });
		send(OPS.notify, next);
	};

	if (tabs.length === 0) return null;

	return (
		<TabsPrimitive value={activeId} onValueChange={onValueChange}>
			{/* A line strip rules the full width; a pill or segmented one is a
			    control and keeps its own. */}
			<TabsList variant={variant} className={variant === "line" ? undefined : "self-start"}>
				{tabs.map((t) => (
					<TabsTrigger key={t.id} value={t.id}>
						{t.label}
					</TabsTrigger>
				))}
			</TabsList>
			{tabs.map((tab) => (
				<TabsContent
					// forceMount keeps inactive bodies rendered so leaf component
					// state survives across tab switches; Radix hides the panel via
					// `data-state="inactive"` when it is not the current tab.
					forceMount
					key={tab.id}
					value={tab.id}
					hidden={tab.id !== activeId}
				>
					{bodies.has(tab.id) ? (
						<FlowProvider flow="block">
							<NodeView path={[...path, tab.id]} />
						</FlowProvider>
					) : null}
				</TabsContent>
			))}
		</TabsPrimitive>
	);
}

export const Tabs: NodeEntry = {
	component: TabsView,
	fill: true,
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
