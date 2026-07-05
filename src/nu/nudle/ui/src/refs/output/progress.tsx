// ProgressRef -- display-only progress bar in [0, 1] with optional caption.
//
// Server-owned. One `write` op carries every mutation; payload is a partial
// map: missing keys leave the slice value untouched. Class-level defaults
// come in on the mount field `props` and seed the slice.

import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function clamp01(n: unknown): number {
	const v = Number(n);
	if (!Number.isFinite(v)) return 0;
	if (v < 0) return 0;
	if (v > 1) return 1;
	return v;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "ProgressRef",
	value: typeof props?.value === "number" ? clamp01(props.value) : 0,
	caption: typeof props?.caption === "string" ? (props.caption as string) : "",
	indeterminate:
		typeof props?.indeterminate === "boolean" ? (props.indeterminate as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				value?: unknown;
				caption?: unknown;
				indeterminate?: unknown;
			};
			if ("value" in p) {
				slice.value = p.value == null ? 0 : clamp01(p.value);
			}
			if ("caption" in p) {
				slice.caption = p.caption == null ? "" : String(p.caption);
			}
			if ("indeterminate" in p) {
				slice.indeterminate = p.indeterminate == null ? false : Boolean(p.indeterminate);
			}
		}),
});

function ProgressView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	const caption = useStore((s) => (s.refs[path]?.caption as string) ?? "");
	const indeterminate = useStore((s) => (s.refs[path]?.indeterminate as boolean) ?? false);
	const pct = Math.round(value * 100);
	return (
		<div className="w-full">
			<div className="h-2 w-full overflow-hidden rounded bg-gray-200">
				{indeterminate ? (
					<div className="h-full w-1/3 animate-pulse bg-blue-500" />
				) : (
					<div className="h-full bg-blue-500" style={{ width: `${pct}%` }} />
				)}
			</div>
			{caption && <div className="mt-1 text-xs text-gray-600">{caption}</div>}
		</div>
	);
}

export const ProgressRef: RefEntry = { factory, component: ProgressView };
