// SliderRef -- numeric slider with min/max/step. Browser is source of truth.
//
// User drags: local slice updates immediately (controlled input).
// On release (pointerup / blur / Enter): notify server. Server-initiated read:
// answer with current value. Server-initiated write: scalar form replaces
// `value`; map form merges any subset of {value, min, max, step, label,
// show_value}. Class-level defaults seed the slice via mount props.

import { OP_NOTIFY } from "../protocol";
import { useStore } from "../store";
import type { RefEntry, SliceFactory } from "./types";

function toFiniteNumber(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

const factory: SliceFactory = (path, ctx, props) => {
	const min = typeof props?.min === "number" ? (props.min as number) : 0;
	const max = typeof props?.max === "number" ? (props.max as number) : 100;
	const step = typeof props?.step === "number" ? (props.step as number) : 1;
	const value = typeof props?.value === "number" ? (props.value as number) : 0;
	return {
		type: "SliderRef",
		value,
		min,
		max,
		step,
		label: typeof props?.label === "string" ? (props.label as string) : "",
		show_value: typeof props?.show_value === "boolean" ? (props.show_value as boolean) : true,
		write: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				// Scalar form: bare number (or nil) replaces just `value`.
				if (v == null || typeof v === "number") {
					slice.value = toFiniteNumber(v, slice.min as number);
					return;
				}
				const p = v as {
					value?: unknown;
					min?: unknown;
					max?: unknown;
					step?: unknown;
					label?: unknown;
					show_value?: unknown;
				};
				if ("min" in p) {
					slice.min = toFiniteNumber(p.min, 0);
				}
				if ("max" in p) {
					slice.max = toFiniteNumber(p.max, 100);
				}
				if ("step" in p) {
					slice.step = toFiniteNumber(p.step, 1);
				}
				if ("value" in p) {
					slice.value = toFiniteNumber(p.value, slice.min as number);
				}
				if ("label" in p) {
					slice.label = p.label == null ? "" : String(p.label);
				}
				if ("show_value" in p) {
					slice.show_value = p.show_value == null ? true : Boolean(p.show_value);
				}
			}),
		get: () => {
			const slice = useStore.getState().refs[path];
			return typeof slice?.value === "number" ? slice.value : 0;
		},
	};
};

function SliderView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	const min = useStore((s) => (s.refs[path]?.min as number) ?? 0);
	const max = useStore((s) => (s.refs[path]?.max as number) ?? 100);
	const step = useStore((s) => (s.refs[path]?.step as number) ?? 1);
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const showValue = useStore((s) => (s.refs[path]?.show_value as boolean) ?? true);
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);

	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });

	return (
		<div className="w-full">
			{label && <div className="mb-1 text-sm">{label}</div>}
			<div className="flex items-center gap-2">
				<input
					type="range"
					className="flex-1"
					min={min}
					max={max}
					step={step}
					value={value}
					onChange={(e) => setLocal(path, Number(e.target.value))}
					onPointerUp={commit}
					onKeyUp={(e) => {
						if (
							e.key === "ArrowLeft" ||
							e.key === "ArrowRight" ||
							e.key === "ArrowUp" ||
							e.key === "ArrowDown" ||
							e.key === "Home" ||
							e.key === "End" ||
							e.key === "PageUp" ||
							e.key === "PageDown" ||
							e.key === "Enter"
						) {
							commit();
						}
					}}
					onBlur={commit}
				/>
				{showValue && <span className="font-mono text-sm tabular-nums">{value}</span>}
			</div>
		</div>
	);
}

export const SliderRef: RefEntry = { factory, component: SliderView };
