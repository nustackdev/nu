// SwitchRef -- boolean toggle (switch affordance). Browser is source of truth.
//
// Same wire shape as CheckboxRef, different renderer: kit Switch primitive.
// The on state is the node's `value` (a real bool); a flip lands it and sends
// `{event: "change"}` at once (./control.ts). A write coerces to a bool, a map
// write merges chrome, the store answers a read from `value`, and `reset`
// puts the declared value back. Readonly keeps the look and takes no flips.

import { Label } from "../../components/ui/field";
import { Switch } from "../../components/ui/switch";
import { type NodeEntry, type NodeProps, useBoolProp } from "../../tree";
import { asBool, resetHandler, useCommit, useControl, valueWrite } from "./control";

function SwitchView({ path }: NodeProps) {
	const checked = useBoolProp(path, "value");
	const c = useControl(path);
	const { pick } = useCommit(path);
	return (
		<div className="inline-flex items-center gap-2">
			<Switch
				{...c.aria}
				checked={checked}
				size={c.size}
				disabled={c.disabled}
				required={c.required}
				autoFocus={c.autoFocus}
				aria-readonly={c.readOnly || undefined}
				onCheckedChange={(next) => {
					if (c.readOnly) return;
					pick(next);
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

export const SwitchRef: NodeEntry = {
	component: SwitchView,
	input: { empty: false },
	handlers: {
		write: valueWrite(asBool),
		reset: resetHandler,
	},
};
