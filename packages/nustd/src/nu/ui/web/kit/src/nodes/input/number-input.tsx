// NumberInputRef -- numeric input with min/max/step and stepper buttons.
// Browser is source of truth.
//
// User types: the node's `value` prop updates immediately (controlled input).
// On commit (blur, Enter, stepper click): notify the server. A server-initiated
// read is answered by the store from `value`. A server-initiated write needs a
// handler: the scalar form is a bare number and nil has to land on the floor
// (`min`, or 0) rather than as null, or the input goes uncontrolled and the
// next read answers null. The map form merges {value, min, max, step, label}
// the way the store merges everything else; those keys are coerced at render.
//
// The slot declares the starting number as `default`, so `value` reads with
// `default` as its fallback until the first write or keystroke lands one.
// Composes the kit NumberInput primitive; the primitive owns steppers +
// keyboard model.

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { NumberInput } from "../../components/ui/number-input";
import {
	type NodeEntry,
	type NodeProps,
	useNumberProp,
	useProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function toFiniteNumber(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

function NumberInputView({ path }: NodeProps) {
	const initial = useNumberProp(path, "default", 0);
	const value = useNumberProp(path, "value", initial);
	const rawMin = useProp<unknown>(path, "min", null);
	const rawMax = useProp<unknown>(path, "max", null);
	const min = typeof rawMin === "number" ? rawMin : null;
	const max = typeof rawMax === "number" ? rawMax : null;
	const step = useNumberProp(path, "step", 1);
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const setValue = useSetValue(path);
	const send = useSend(path);
	const id = useId();

	const commit = () => send(OPS.notify);

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
					setValue(next ?? 0);
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

export const NumberInputRef: NodeEntry = {
	component: NumberInputView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload && typeof payload === "object" && !Array.isArray(payload)) {
					Object.assign(props, payload);
					if ("value" in payload) {
						props.value = toFiniteNumber(props.value, toFiniteNumber(props.min, 0));
					}
					return;
				}
				props.value = toFiniteNumber(payload, toFiniteNumber(props.min, 0));
			}),
	},
};
