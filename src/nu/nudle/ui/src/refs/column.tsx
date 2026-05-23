// Column -- vertical Section. Stacks child Refs with gap, alignment,
// justification, and padding. Display-only; chrome props are seeded from
// the mount `props` and updated via `write`. Children are nested wire
// paths from the mount field entry's `fields` list (one slice per child,
// registered recursively at mount time).

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { renderers } from "../refs";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

const ALIGN_CLASSES: Record<string, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
	stretch: "items-stretch",
};

const JUSTIFY_CLASSES: Record<string, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
	between: "justify-between",
	around: "justify-around",
};

function numOr(v: unknown, fallback: number): number {
	const n = Number(v);
	return Number.isFinite(n) ? n : fallback;
}

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Column",
	value: null,
	gap: numOr(props?.gap, 4),
	align: typeof props?.align === "string" ? (props.align as string) : "stretch",
	justify: typeof props?.justify === "string" ? (props.justify as string) : "start",
	padding: numOr(props?.padding, 0),
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				gap?: unknown;
				align?: unknown;
				justify?: unknown;
				padding?: unknown;
			};
			if ("gap" in p) slice.gap = numOr(p.gap, 4);
			if ("align" in p) slice.align = p.align == null ? "stretch" : String(p.align);
			if ("justify" in p) slice.justify = p.justify == null ? "start" : String(p.justify);
			if ("padding" in p) slice.padding = numOr(p.padding, 0);
		}),
});

function ColumnView({ path }: { path: string }) {
	const gap = useStore((s) => numOr(s.refs[path]?.gap, 4));
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "stretch");
	const justify = useStore((s) => (s.refs[path]?.justify as string) ?? "start");
	const padding = useStore((s) => numOr(s.refs[path]?.padding, 0));
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const cls = `flex flex-col gap-${gap} p-${padding} ${alignCls} ${justifyCls}`;

	return (
		<div className={cls}>
			{childPaths.map((cp) => {
				const childSlice = refs[cp];
				if (!childSlice) {
					return (
						<div key={cp} className="text-xs text-destructive font-mono">
							no ref at {cp}
						</div>
					);
				}
				const Comp = renderers[childSlice.type];
				if (!Comp) {
					return (
						<div key={cp} className="text-xs text-destructive font-mono">
							no renderer for {childSlice.type}
						</div>
					);
				}
				return (
					<ErrorBoundary key={cp} label={`${cp} (${childSlice.type})`}>
						<Comp path={cp} />
					</ErrorBoundary>
				);
			})}
		</div>
	);
}

export const Column: RefEntry = { factory, component: ColumnView };
