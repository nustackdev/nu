// NumberInputRef -- numeric input with min/max/step and stepper buttons.
// Browser is source of truth.
//
// Typing is a local edit (the node's `value` prop follows the field). Blur
// commits, a stepper click or an arrow key commits at once, and Enter
// commits, then submits and asks an enclosing Form to submit. See
// ./control.ts for the contract.
//
// Empty is null, not 0: a cleared field holds null, a read answers null and
// a form's values carry it, so "no number" never reads as a zero. A
// server-initiated write needs a handler: the scalar form is a bare number,
// nil or anything that is not a finite number lands as null. The map form merges
// {value, min, max, step, label, ...} the way the store merges everything
// else. `reset` puts the declared value back. Composes the kit NumberInput
// primitive; the primitive owns steppers and the keyboard model.

import { Label } from "../../components/ui/field";
import { NumberInput } from "../../components/ui/number-input";
import { type NodeEntry, type NodeProps, useNumberProp, useProp } from "../../tree";
import { isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

function toNumberOrNull(n: unknown): number | null {
	if (n == null || n === "") return null;
	const v = Number(n);
	return Number.isFinite(v) ? v : null;
}

function NumberInputView({ path }: NodeProps) {
	const rawMin = useProp<unknown>(path, "min", null);
	const rawMax = useProp<unknown>(path, "max", null);
	const min = typeof rawMin === "number" ? rawMin : null;
	const max = typeof rawMax === "number" ? rawMax : null;
	const value = toNumberOrNull(useProp<unknown>(path, "value", null));
	const step = useNumberProp(path, "step", 1);
	const c = useControl(path);
	const { edit, commit, pick, submit } = useCommit(path);

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<NumberInput
				{...c.aria}
				value={value}
				size={c.size}
				placeholder={c.placeholder}
				min={min ?? undefined}
				max={max ?? undefined}
				step={step}
				disabled={c.disabled}
				readOnly={c.readOnly}
				required={c.required}
				autoFocus={c.autoFocus}
				invalid={c.invalid}
				onValueChange={(next) => edit(next)}
				onValueCommit={pick}
				onBlur={commit}
				onKeyDown={(e) => {
					if (!isEnter(e)) return;
					e.preventDefault();
					submit(e.currentTarget);
				}}
			/>
		</div>
	);
}

export const NumberInputRef: NodeEntry = {
	component: NumberInputView,
	fill: true,
	input: { empty: null },
	handlers: {
		write: valueWrite(toNumberOrNull),
		reset: resetHandler,
	},
};
