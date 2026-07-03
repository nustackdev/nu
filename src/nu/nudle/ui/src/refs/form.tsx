// Form -- semantic <form> Section. Stacks child Refs vertically with gap,
// padding, and cross-axis alignment. Display-only, server-owned. The
// onSubmit handler exists solely to block the browser's native reload on
// Enter; submit logic lives on a child ButtonRef.

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

	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.stretch;
	const cls = `flex flex-col gap-${gap} p-${padding} ${alignCls}`;

	return (
		<form onSubmit={(e) => e.preventDefault()} className={cls}>
			{title ? <h3 className="text-sm font-semibold mb-2">{title}</h3> : null}
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
		</form>
	);
}

export const Form: RefEntry = { factory, component: FormView };
