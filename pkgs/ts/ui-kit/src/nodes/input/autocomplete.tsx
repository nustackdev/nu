// AutocompleteRef -- text input with a suggestion list. Browser is source of
// truth.
//
// The value is free text on the node's `value`, like InputRef: typing edits
// it locally, blur commits (`{event: "change"}` if it moved), Enter submits
// (change first if it moved, then `{event: "submit"}`, then the enclosing
// Form). The suggestions come from `options` (strings or {value,label}
// maps, replaced by a map write) and filter on what is typed. Enter on a
// highlighted suggestion picks it instead: its value lands and a change goes
// at once, no submit. Arrow keys move the highlight, nothing is highlighted
// until one does, so plain typing plus Enter submits the text as typed.
//
// A bare write sets the text (nil clears), the store answers a read from
// `value`, `reset` puts the declared text back. Composes the kit
// Autocomplete primitive. The entry is `fill`, like InputRef.

import { useMemo } from "react";
import { Autocomplete } from "../../components/ui/autocomplete";
import { Label } from "../../components/ui/field";
import { type NodeEntry, type NodeProps, useListProp, useStringProp } from "../../tree";
import { asText, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";
import { normalizeOptions } from "./select";

function AutocompleteView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const c = useControl(path);
	const { edit, commit, pick, submit } = useCommit(path);
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<Autocomplete
				{...c.aria}
				options={options}
				value={value}
				size={c.size}
				placeholder={c.placeholder || undefined}
				disabled={c.disabled}
				readOnly={c.readOnly}
				required={c.required}
				autoFocus={c.autoFocus}
				invalid={c.invalid}
				onValueChange={edit}
				onPick={pick}
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

export const AutocompleteRef: NodeEntry = {
	component: AutocompleteView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
