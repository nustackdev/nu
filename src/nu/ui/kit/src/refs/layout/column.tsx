// Column -- vertical Section. Stacks child Refs with gap, alignment,
// justification, and padding. Display-only; chrome props are seeded from
// the mount `props` and updated via `write`. Children are nested wire
// paths from the mount field entry's `fields` list (one slice per child,
// registered recursively at mount time).
//
// TODO(retune): the legacy Column Ref accepts numeric `gap` / `padding`
// (0..12+) and templates raw Tailwind class names. Under Tailwind v4 those
// arbitrary utilities need the JIT to see them at build time. We map the
// discrete step ladder (0/1/2/3/4/5/6/8/10/12) statically here so every
// possible class name is present in the compiled bundle. A proper `Stack`
// primitive with named tokens (`gap="md"`) is the follow-up; the wire
// contract stays numeric until then.

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

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES[4];
	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES[0];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const justifyCls = JUSTIFY_CLASSES[justify] ?? JUSTIFY_CLASSES.start;
	const cls = `flex flex-col ${gapCls} ${padCls} ${alignCls} ${justifyCls}`;

	return (
		<div className={cls}>
			{childPaths.map((cp) => {
				const childSlice = refs[cp];
				if (!childSlice) {
					return (
						<div key={cp} className="text-xs text-status-danger font-mono">
							no ref at {cp}
						</div>
					);
				}
				const Comp = renderers[childSlice.type];
				if (!Comp) {
					return (
						<div key={cp} className="text-xs text-status-danger font-mono">
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
