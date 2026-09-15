// InputRef -- text input. Browser is source of truth.
//
// User types: the node's `value` prop updates immediately (controlled input).
// On blur or Enter: notify the server. Server-initiated read is answered by
// the store from `value`, so there is nothing to write for it here. A
// server-initiated write replaces the value (canonical / reset) and is the
// one op that needs a handler: a null write must land as "" so the input
// does not go uncontrolled.
//
// Chrome (label, placeholder, type, max_length, mono) is just more props,
// declared at the slot and read at render.

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { Input } from "../../components/ui/input";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function InputView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const inputType = useStringProp(path, "type", "text");
	const maxLength = useProp<number | null>(path, "max_length", null);
	const mono = useBoolProp(path, "mono");
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
			<Input
				id={id}
				type={inputType}
				placeholder={placeholder}
				maxLength={maxLength ?? undefined}
				value={value}
				className={mono ? "font-mono" : undefined}
				onChange={(e) => setValue(e.target.value)}
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

export const InputRef: NodeEntry = {
	component: InputView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				props.value = payload == null ? "" : String(payload);
			}),
	},
};
