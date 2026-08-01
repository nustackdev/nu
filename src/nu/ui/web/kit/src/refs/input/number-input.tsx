// NumberInputRef -- numeric input with min/max/step and stepper buttons.
// Browser is source of truth.
//
// User types: local slice updates immediately (controlled input).
// On commit (blur, Enter, stepper click): clamp to [min, max] if set and notify
// server. Server-initiated read: answer with current value. Server-initiated
// write: scalar form replaces `value`; map form merges any subset of
// {value, min, max, step, label}. Composes the kit NumberInput primitive;
// the primitive owns steppers + keyboard model.

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { NumberInput } from "../../components/ui/number-input";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function toFiniteNumber(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

const factory: SliceFactory = (path, ctx, props) => {
	const min = typeof props?.min === "number" ? (props.min as number) : null;
	const max = typeof props?.max === "number" ? (props.max as number) : null;
	const step = typeof props?.step === "number" ? (props.step as number) : 1;
	const value = typeof props?.default === "number" ? (props.default as number) : 0;
	return {
		type: "NumberInputRef",
		value,
		min,
		max,
		step,
		label: typeof props?.label === "string" ? (props.label as string) : "",
		placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
		write: (v) =>
			ctx.set((refs) => {
				const slice = refs[path];
				if (!slice) return;
				const floor = typeof slice.min === "number" ? (slice.min as number) : 0;
				// Scalar form: bare number (or nil) replaces just `value`.
				if (v == null || typeof v === "number") {
					slice.value = toFiniteNumber(v, floor);
					return;
				}
				const p = v as {
					value?: unknown;
					min?: unknown;
					max?: unknown;
					step?: unknown;
					label?: unknown;
				};
				if ("min" in p) {
					slice.min = p.min == null ? null : toFiniteNumber(p.min, 0);
				}
				if ("max" in p) {
					slice.max = p.max == null ? null : toFiniteNumber(p.max, 0);
				}
				if ("step" in p) {
					slice.step = toFiniteNumber(p.step, 1);
				}
				if ("value" in p) {
					const newFloor = typeof slice.min === "number" ? (slice.min as number) : 0;
					slice.value = toFiniteNumber(p.value, newFloor);
				}
				if ("label" in p) {
					slice.label = p.label == null ? "" : String(p.label);
				}
			}),
		get: () => {
			const slice = useStore.getState().refs[path];
			return typeof slice?.value === "number" ? slice.value : 0;
		},
	};
};

function NumberInputView({ path }: { path: string }) {
	const value = useStore((s) => (s.refs[path]?.value as number) ?? 0);
	const min = useStore((s) => s.refs[path]?.min as number | null | undefined);
	const max = useStore((s) => s.refs[path]?.max as number | null | undefined);
	const step = useStore((s) => (s.refs[path]?.step as number) ?? 1);
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const setLocal = useStore((s) => s.setLocal);
	const send = useStore((s) => s.send);
	const id = useId();

	const commit = () => send({ op: OP_NOTIFY, ref: path, payload: null });

	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<NumberInput
				id={id}
				value={value}
				placeholder={placeholder}
				min={min ?? undefined}
				max={max ?? undefined}
				step={step}
				onValueChange={(next) => {
					setLocal(path, next ?? 0);
					commit();
				}}
				onBlur={commit}
				onKeyDown={(e) => {
					if (e.key === "Enter") {
						commit();
						(e.target as HTMLInputElement).blur();
					}
				}}
			/>
		</div>
	);
}

export const NumberInputRef: RefEntry = { factory, component: NumberInputView };
