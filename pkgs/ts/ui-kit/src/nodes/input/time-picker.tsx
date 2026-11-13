// TimePickerRef -- time of day input. Browser is source of truth.
//
// The value is "HH:MM" on the node's `value` ("HH:MM:SS" when `step` is under
// a minute), or "" for none, both ways on the wire. The field is text-like:
// typing is a local edit, blur commits (a change, when it moved), Enter
// commits, then submits and asks an enclosing Form to submit. The clear
// button lands "" and sends its change at once. `min`, `max` and `step`
// (seconds) are the native constraints. A write replaces the value (nil
// lands as ""), a map write merges chrome, and `reset` puts the declared
// value back. See ./control.ts for the contract.
//
// Composes the kit TimePicker (a native time field in kit Input chrome).

import { Label } from "../../components/ui/field";
import { TimePicker } from "../../components/ui/time-picker";
import { type NodeEntry, type NodeProps, useBoolProp, useProp, useStringProp } from "../../tree";
import { asText, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

function TimePickerView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const min = useStringProp(path, "min");
	const max = useStringProp(path, "max");
	const step = useProp<unknown>(path, "step", null);
	const clearable = useBoolProp(path, "clearable", true);
	const c = useControl(path);
	const { edit, commit, pick, submit } = useCommit(path);
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<TimePicker
				{...c.aria}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled}
				readOnly={c.readOnly}
				required={c.required}
				autoFocus={c.autoFocus}
				min={min || undefined}
				max={max || undefined}
				step={typeof step === "number" && step > 0 ? step : undefined}
				clearable={clearable}
				value={value}
				onValueChange={edit}
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

export const TimePickerRef: NodeEntry = {
	component: TimePickerView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
