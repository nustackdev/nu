// TabsRef -- tab strip plus active body. Section-shaped: children come from
// the mount entry's nested `fields` and pair with `tabs[i]` by index.
//
// Server-owned tabs / active (with optimistic local active on click).
// Two inbound ops:
//   set_tabs   replace the tabs list wholesale
//   set_active set the active tab id (server pin / confirmation)
// One outbound notify on user click: payload is the clicked tab id. The
// server may mirror it back via set_active. Inactive bodies stay mounted
// (via forceMount + `hidden`) so leaf slices keep their local state.
// Composes the kit Tabs primitive family (Radix Tabs under the hood).

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import {
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from "../../components/ui/tabs";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

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

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "TabsRef",
	value: null,
	tabs: normalizeTabs(props?.tabs),
	active: typeof props?.active === "string" ? (props.active as string) : "",
	children: Array.isArray(children) ? [...children] : [],
	set_tabs: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.tabs = normalizeTabs(v);
		}),
	set_active: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.active = v == null ? "" : String(v);
		}),
	setActive: (id: string) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.active = id;
		}),
});

function TabsView({ path }: { path: string }) {
	const tabs = useStore((s) => (s.refs[path]?.tabs as Tab[]) ?? []);
	const active = useStore((s) => (s.refs[path]?.active as string) ?? "");
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);
	const send = useStore((s) => s.send);

	const activeId = active && tabs.some((t) => t.id === active) ? active : (tabs[0]?.id ?? "");
	const n = Math.min(tabs.length, childPaths.length);

	const onValueChange = (next: string) => {
		const setter = useStore.getState().refs[path]?.setActive as
			| ((id: string) => void)
			| undefined;
		if (setter) setter(next);
		send({ op: OP_NOTIFY, ref: path, payload: next });
	};

	if (n === 0) return null;

	return (
		<Tabs value={activeId} onValueChange={onValueChange}>
			<TabsList variant="line">
				{tabs.slice(0, n).map((t) => (
					<TabsTrigger key={t.id} value={t.id} variant="line">
						{t.label}
					</TabsTrigger>
				))}
			</TabsList>
			{Array.from({ length: n }).map((_, i) => {
				const cp = childPaths[i];
				const tab = tabs[i];
				const childSlice = refs[cp];
				return (
					<TabsContent
						// forceMount keeps inactive bodies rendered so leaf slice state
						// survives across tab switches; Radix hides the panel via
						// `data-state="inactive"` when it is not the current tab.
						forceMount
						key={cp}
						value={tab.id}
						hidden={tab.id !== activeId}
					>
						{!childSlice ? (
							<div className="text-xs text-status-danger font-mono">no ref at {cp}</div>
						) : !renderers[childSlice.type] ? (
							<div className="text-xs text-status-danger font-mono">
								no renderer for {childSlice.type}
							</div>
						) : (
							<ErrorBoundary label={`${cp} (${childSlice.type})`}>
								{(() => {
									const Comp = renderers[childSlice.type];
									return <Comp path={cp} />;
								})()}
							</ErrorBoundary>
						)}
					</TabsContent>
				);
			})}
		</Tabs>
	);
}

export const TabsRef: RefEntry = { factory, component: TabsView };
