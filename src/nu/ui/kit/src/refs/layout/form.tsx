// Form -- semantic <form> Section. Stacks child Refs vertically with gap,
// padding, and cross-axis alignment. Display-only, server-owned. The
// onSubmit handler exists solely to block the browser's native reload on
// Enter; submit logic lives on a child ButtonRef.
//
// TODO(retune): same dynamic-class concern as Column: numeric gap /
// padding template raw Tailwind class names. We map the discrete step
// ladder statically here so the JIT sees every candidate at build time.
// A `Form` primitive with named tokens is the follow-up.

import { ErrorBoundary } from "../../components/ErrorBoundary";
import { Heading } from "../../components/ui/heading";
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

function numOr(v: unknown, fallback: number): number {
	const n = Number(v);
	return Number.isFinite(n) ? n : fallback;
}

function strOr(v: unknown, fallback: string): string {
	if (v == null) return fallback;
	return typeof v === "string" ? v : String(v);
}

const factory: SliceFactory = (path, ctx, props, children) => ({
	type: "Form",
	value: null,
	title: strOr(props?.title, ""),
	gap: numOr(props?.gap, 4),
	padding: numOr(props?.padding, 0),
	align: typeof props?.align === "string" ? (props.align as string) : "stretch",
	children: Array.isArray(children) ? [...children] : [],
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				title?: unknown;
				gap?: unknown;
				padding?: unknown;
				align?: unknown;
			};
			if ("title" in p) slice.title = strOr(p.title, "");
			if ("gap" in p) slice.gap = numOr(p.gap, 4);
			if ("padding" in p) slice.padding = numOr(p.padding, 0);
			if ("align" in p) slice.align = p.align == null ? "stretch" : String(p.align);
		}),
});

function FormView({ path }: { path: string }) {
	const title = useStore((s) => (s.refs[path]?.title as string) ?? "");
	const gap = useStore((s) => numOr(s.refs[path]?.gap, 4));
	const padding = useStore((s) => numOr(s.refs[path]?.padding, 0));
	const align = useStore((s) => (s.refs[path]?.align as string) ?? "stretch");
	const childPaths = useStore((s) => (s.refs[path]?.children as string[]) ?? []);
	const refs = useStore((s) => s.refs);

	const gapCls = GAP_CLASSES[gap] ?? GAP_CLASSES[4];
	const padCls = PADDING_CLASSES[padding] ?? PADDING_CLASSES[0];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const cls = `flex flex-col ${gapCls} ${padCls} ${alignCls}`;

	return (
		<form onSubmit={(e) => e.preventDefault()} className={cls}>
			{title ? (
				<Heading as="h3" size="xl" className="mb-2">
					{title}
				</Heading>
			) : null}
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
		</form>
	);
}

export const Form: RefEntry = { factory, component: FormView };
