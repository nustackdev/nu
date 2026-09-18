// TextAreaRef -- multi-line text input. Browser is source of truth.
//
// User types: the node's `value` prop updates immediately (controlled).
// Commit moments (blur, cmd/ctrl-enter): notify the server. A server-initiated
// read is answered by the store from `value`. A server-initiated write
// replaces the value (canonical / reset) and is the one op that needs a
// handler: a null write must land as "" so the textarea does not go
// uncontrolled and a following read answers "" rather than null.
//
// Chrome (label, placeholder, rows, max_length, auto_resize, mono) is just
// more props, declared at the slot and read at render. Composes the kit
// TextArea primitive; the primitive owns autoResize via CSS
// `field-sizing: content`.

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { TextArea } from "../../components/ui/text-area";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function TextAreaView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const rows = useNumberProp(path, "rows", 4);
	const maxLength = useProp<number | null>(path, "max_length", null);
	const autoResize = useBoolProp(path, "auto_resize");
	const mono = useBoolProp(path, "mono");
	const setValue = useSetValue(path);
	const send = useSend(path);
	const id = useId();

	const commit = () => send(OPS.notify);
	const cls = [autoResize ? "[field-sizing:content]" : null, mono ? "font-mono" : null]
		.filter(Boolean)
		.join(" ");

	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<TextArea
				id={id}
				value={value}
				rows={rows}
				placeholder={placeholder}
				maxLength={maxLength ?? undefined}
				className={cls || undefined}
				onChange={(e) => setValue(e.target.value)}
				onBlur={commit}
				onKeyDown={(e) => {
					if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
						commit();
						(e.target as HTMLTextAreaElement).blur();
					}
				}}
			/>
		</div>
	);
}

export const TextAreaRef: NodeEntry = {
	component: TextAreaView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				props.value = payload == null ? "" : String(payload);
			}),
	},
};
