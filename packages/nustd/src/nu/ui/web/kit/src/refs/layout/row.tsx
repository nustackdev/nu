// RowRef -- layout primitive. Arranges child Refs horizontally.
//
// Display-only, server-owned. One `write` op carries every mutation; payload
// is a partial map. Children are absolute wire paths into the same mount
// payload; the renderer looks each up in the registry and renders it.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { renderers } from "../../refs";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	8: "gap-8",
	10: "gap-10",
	12: "gap-12",
};

const PADDING_CLASSES: Record<number, string> = {
	0: "p-0",
	1: "p-1",
	2: "p-2",
	3: "p-3",
	4: "p-4",
	5: "p-5",
	6: "p-6",
	8: "p-8",
	10: "p-10",
	12: "p-12",
};

const ALIGN_CLASSES: Record<string, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
	stretch: "items-stretch",
	baseline: "items-baseline",
};

const JUSTIFY_CLASSES: Record<string, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
	between: "justify-between",
	around: "justify-around",
	evenly: "justify-evenly",
};

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Row",
	value: null,
	gap: typeof props?.gap === "number" ? (props.gap as number) : 4,
	align: typeof props?.align === "string" ? (props.align as string) : "center",
	justify: typeof props?.justify === "string" ? (props.justify as string) : "start",
	wrap: typeof props?.wrap === "boolean" ? (props.wrap as boolean) : false,
	padding: typeof props?.padding === "number" ? (props.padding as number) : 0,
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				gap?: unknown;
				align?: unknown;
				justify?: unknown;
				wrap?: unknown;
				padding?: unknown;
			};
			if ("gap" in p) slice.gap = p.gap == null ? 4 : Number(p.gap);
			if ("align" in p) slice.align = p.align == null ? "center" : String(p.align);
			if ("justify" in p) slice.justify = p.justify == null ? "start" : String(p.justify);
			if ("wrap" in p) slice.wrap = p.wrap == null ? false : Boolean(p.wrap);
			if ("padding" in p) slice.padding = p.padding == null ? 0 : Number(p.padding);
		}),
});

function RowView({ path }: { path: string }) {
	const gap = useStore((s) => (s.refs[path]?.gap as number) ?? 4);
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "center");
	const justify = useStore((s) => (s.refs[path]?.justify as string) ?? "start");
	const wrap = useStore((s) => (s.refs[path]?.wrap as boolean) ?? false);
	const padding = useStore((s) => (s.refs[path]?.padding as number) ?? 0);
	const children = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES[4];
	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES[0];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.center;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const wrapCls = wrap ? "flex-wrap" : "flex-nowrap";

	return (
		<div className={`flex flex-row ${gapCls} ${padCls} ${alignCls} ${justifyCls} ${wrapCls}`}>
			{children.map((childPath) => {
				const childSlice = refs[childPath];
				if (!childSlice) {
					return (
						<div key={childPath} className="text-xs text-status-danger font-mono">
							no ref at {childPath}
						</div>
					);
				}
				const Comp = renderers[childSlice.type];
				if (!Comp) {
					return (
						<div key={childPath} className="text-xs text-status-danger font-mono">
							no renderer for {childSlice.type}
						</div>
					);
				}
				return (
					<ErrorBoundary key={childPath} label={`${childPath} (${childSlice.type})`}>
						<Comp path={childPath} />
					</ErrorBoundary>
				);
			})}
		</div>
	);
}

export const Row: RefEntry = { factory, component: RowView };
