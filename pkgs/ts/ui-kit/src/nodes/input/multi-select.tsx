// MultiSelectRef -- dropdown multi choice with a search field. Browser is
// source of truth.
//
// The picked option values are the node's `value`, a list in option order
// ([] for none). Each pick in the list ticks one option on or off, lands the
// list and sends `{event: "change"}` at once (./control.ts); the list stays
// open for the next pick. Writes, read and `reset` match CheckboxGroupRef:
// a list replaces, a lone string picks one, nil clears, a map merges chrome
// (how `options` is replaced).
//
// The trigger is the real control: it takes the Field's id and aria, and
// `<label for>` names it. Composes the kit MultiSelect primitive (the kit
// Combobox underneath). The entry is `fill`, like SelectRef.

import { useMemo } from "react";
import { Label } from "../../components/ui/field";
import { MultiSelect } from "../../components/ui/multi-select";
import { type NodeEntry, type NodeProps, useListProp } from "../../tree";
import { asList } from "./checkbox-group";
import { resetHandler, useCommit, useControl, valueWrite } from "./control";
import { normalizeOptions } from "./select";

function MultiSelectView({ path }: NodeProps) {
	const picked = useListProp<string>(path, "value");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const c = useControl(path);
	const { pick } = useCommit(path);
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<MultiSelect
				{...c.aria}
				options={options}
				value={picked}
				placeholder={c.placeholder}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled}
				autoFocus={c.autoFocus}
				aria-readonly={c.readOnly || undefined}
				onValueChange={(next) => {
					if (!c.readOnly) pick(next);
				}}
			/>
		</div>
	);
}

export const MultiSelectRef: NodeEntry = {
	component: MultiSelectView,
	fill: true,
	input: { empty: [] },
	handlers: {
		write: valueWrite(asList),
		reset: resetHandler,
	},
};
