// TextAreaRef -- multi-line text input. Browser is source of truth.
//
// User types: the node's `value` prop updates immediately (controlled). Blur
// commits. cmd/ctrl+Enter commits, then submits, and plain Enter is a newline.
// `submit_on="enter"` turns it into a chat composer: Enter submits and
// shift+Enter is the newline. Focus stays put either way. See ./control.ts.
//
// A server-initiated write replaces the value: a null write must land as ""
// so the textarea does not go uncontrolled and a following read answers "".
// A map write merges chrome. `reset` puts the declared value back.
//
// Chrome (label, placeholder, rows, max_length, auto_resize, mono, the
// common props) is just more props. Composes the kit TextArea primitive; the
// primitive owns autoResize via CSS `field-sizing: content`.

import { Label } from "../../components/ui/field";
import { TextArea } from "../../components/ui/text-area";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";
import { asText, isEnter, resetHandler, useCommit, useControl, valueWrite } from "./control";

function TextAreaView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const rows = useNumberProp(path, "rows", 4);
	const maxLength = useProp<number | null>(path, "max_length", null);
	const autoResize = useBoolProp(path, "auto_resize");
	const mono = useBoolProp(path, "mono");
	const submitOn = useStringProp(path, "submit_on", "mod+enter");
	const c = useControl(path);
	const { edit, commit, submit } = useCommit(path);

	const cls = [autoResize ? "[field-sizing:content]" : null, mono ? "font-mono" : null]
		.filter(Boolean)
		.join(" ");

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<TextArea
				{...c.aria}
				value={value}
				rows={rows}
				size={c.size}
				placeholder={c.placeholder}
				maxLength={maxLength ?? undefined}
				disabled={c.disabled}
				readOnly={c.readOnly}
				required={c.required}
				autoFocus={c.autoFocus}
				invalid={c.invalid}
				className={cls || undefined}
				onChange={(e) => edit(e.target.value)}
				onBlur={commit}
				onKeyDown={(e) => {
					if (!isEnter(e)) return;
					const mod = e.metaKey || e.ctrlKey;
					const sends = submitOn === "enter" ? !e.shiftKey : mod;
					if (!sends) return;
					e.preventDefault();
					submit(e.currentTarget);
				}}
			/>
		</div>
	);
}

export const TextAreaRef: NodeEntry = {
	component: TextAreaView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
