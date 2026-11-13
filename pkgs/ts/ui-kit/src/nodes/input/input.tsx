// InputRef -- text input. Browser is source of truth.
//
// User types: the node's `value` prop updates immediately (controlled input),
// so a read sees what is under the caret. Blur commits (`{event: "change"}`,
// only when the value moved). Enter commits, then submits (`{event:
// "submit"}`), then asks an enclosing Form to submit; focus stays put. See
// ./control.ts for the contract every input shares.
//
// A server-initiated write replaces the value and is the one op that needs a
// handler: a null write must land as "" so the input does not go
// uncontrolled. `reset` puts the declared value back.
//
// Chrome (label, placeholder, type, max_length, mono, and the common
// disabled / readonly / required / autofocus / size) is just more props,
// declared at the slot and read at render.
//
// Types. `text`, `email`, `url`, `tel` and `number` are the native field
// (the browser picks the keyboard and checks the format). `search` is the
// kit SearchInput: a clear button while there is text, and Escape clears;
// clearing lands "" and commits at once (a change, if that moved it). `password` is
// the kit PasswordInput, with a show / hide toggle. The value is text for
// every type.

import type * as React from "react";
import { Label } from "../../components/ui/field";
import { Input } from "../../components/ui/input";
import { PasswordInput, SearchInput } from "../../components/ui/input-affix";
import { type NodeEntry, type NodeProps, useBoolProp, useProp, useStringProp } from "../../tree";
import { asText, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

function InputView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const inputType = useStringProp(path, "type", "text");
	const maxLength = useProp<number | null>(path, "max_length", null);
	const mono = useBoolProp(path, "mono");
	const c = useControl(path);
	const { edit, commit, submit } = useCommit(path);
	const field = {
		...c.aria,
		size: c.size,
		placeholder: c.placeholder,
		maxLength: maxLength ?? undefined,
		disabled: c.disabled,
		readOnly: c.readOnly,
		required: c.required,
		autoFocus: c.autoFocus,
		invalid: c.invalid,
		value,
		className: mono ? "font-mono" : undefined,
		onChange: (e: React.ChangeEvent<HTMLInputElement>) => edit(e.target.value),
		onBlur: commit,
		onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
			if (!isEnter(e)) return;
			e.preventDefault();
			submit(e.currentTarget);
		},
	};
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			{inputType === "search" ? (
				<SearchInput
					{...field}
					onClear={() => {
						edit("");
						commit();
					}}
				/>
			) : inputType === "password" ? (
				<PasswordInput {...field} />
			) : (
				<Input {...field} type={inputType} />
			)}
		</div>
	);
}

export const InputRef: NodeEntry = {
	component: InputView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
