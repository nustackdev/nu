// TabsRef -- tab strip plus active body. Section-shaped: children come from
// the mount entry's nested `fields` and pair with `tabs[i]` by index.
//
// Server-owned tabs / active (with optimistic local active on click).
// Two inbound ops:
//   store_tabs   replace the tabs list wholesale
//   store_active set the active tab id (server pin / confirmation)
// One outbound notify on user click: payload is the clicked tab id. The
// server may mirror it back via store_active. Inactive bodies stay mounted
// (display: none) so leaf slices keep their local state.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { OP_NOTIFY } from "@nustackdev/ui-core";
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
	store_tabs: (v: unknown) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			slice.tabs = normalizeTabs(v);
		}),
	store_active: (v: unknown) =>
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

	const onClick = (id: string) => {
		const setter = useStore.getState().refs[path]?.setActive as ((id: string) => void) | undefined;
		if (setter) setter(id);
		send({ op: OP_NOTIFY, ref: path, payload: id });
	};

	return (
		<div className="flex flex-col">
			<div role="tablist" className="flex gap-1 border-b">
				{tabs.map((t) => (
					<button
						key={t.id}
						type="button"
						role="tab"
						aria-selected={t.id === activeId}
						onClick={() => onClick(t.id)}
						className={
							t.id === activeId
								? "border-b-2 border-primary px-3 py-2 text-sm"
								: "px-3 py-2 text-sm text-muted-foreground"
						}
					>
						{t.label}
					</button>
				))}
			</div>
			<div className="pt-3">
				{Array.from({ length: n }).map((_, i) => {
					const cp = childPaths[i];
					const tid = tabs[i].id;
					const childSlice = refs[cp];
					const style = tid === activeId ? undefined : { display: "none" };
					if (!childSlice) {
						return (
							<div key={cp} style={style} className="text-xs text-destructive font-mono">
								no ref at {cp}
							</div>
						);
					}
					const Comp = renderers[childSlice.type];
					if (!Comp) {
						return (
							<div key={cp} style={style} className="text-xs text-destructive font-mono">
								no renderer for {childSlice.type}
							</div>
						);
					}
					return (
						<div key={cp} style={style}>
							<ErrorBoundary label={`${cp} (${childSlice.type})`}>
								<Comp path={cp} />
							</ErrorBoundary>
						</div>
					);
				})}
			</div>
		</div>
	);
}

export const TabsRef: RefEntry = { factory, component: TabsView };
