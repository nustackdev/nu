// CheckboxRef -- boolean toggle. Browser is source of truth.
//
// The checked state is the node's `value` (a real bool). A toggle lands it
// and sends `{event: "change"}` at once (./control.ts). A write lands the
// payload on `value`, coerced to a bool so the box never goes uncontrolled; a
// map write merges chrome. The store answers a read from `value`. `reset`
// puts the declared value back.
//
// Composes the kit Checkbox primitive (Radix under the hood). Readonly keeps
// the look and takes no toggles.

import { Checkbox } from "../../components/ui/checkbox";
import { Label } from "../../components/ui/field";
import { type NodeEntry, type NodeProps, useBoolProp } from "../../tree";
import { asBool, resetHandler, useCommit, useControl, valueWrite } from "./control";

function CheckboxView({ path }: NodeProps) {
	const checked = useBoolProp(path, "value");
	const c = useControl(path);
	const { pick } = useCommit(path);
	return (
		<div className="inline-flex items-center gap-2">
			<Checkbox
				{...c.aria}
				checked={checked}
				size={c.size}
				disabled={c.disabled}
				required={c.required}
				autoFocus={c.autoFocus}
				invalid={c.invalid}
				aria-readonly={c.readOnly || undefined}
				onCheckedChange={(next) => {
					if (c.readOnly) return;
					pick(next === true);
				}}
			/>
			{c.label && (
				<Label htmlFor={c.id} inline required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
		</div>
	);
}

export const CheckboxRef: NodeEntry = {
	component: CheckboxView,
	input: { empty: false },
	handlers: {
		write: valueWrite(asBool),
		reset: resetHandler,
	},
};
