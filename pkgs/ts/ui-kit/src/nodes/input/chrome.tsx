// What every input entry gets on top of its own node, applied once over the
// whole set in ./index.ts so no input has to ask for it:
//
// - the `focus` op (./control.ts `focusHandler`);
// - an error under a control that has no Field around it. A failed check or
//   a program's error lands on the control's Field when there is one (the
//   Field draws it). A bare control gets the kit Field chrome put around it
//   the first time one lands, which ties the message to the control the same
//   way (`aria-describedby`, invalid). The chrome then stays for the life of
//   the node, so clearing the error, or typing that clears a check, never
//   remounts the control under the caret. A node that draws its own error
//   (`input.ownsError`, InlineEdit) is left as it is.

import { type ComponentType, useRef } from "react";
import { Field as FieldChrome, useFieldControl } from "../../components/ui/field";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";
import { focusHandler } from "./control";

function withError(View: ComponentType<NodeProps>): ComponentType<NodeProps> {
	function Errored({ path }: NodeProps) {
		const field = useFieldControl();
		const error = useStringProp(path, "error");
		const check = useStringProp(path, "check");
		const message = error || check;
		const framed = useRef(false);
		if (!field && message) framed.current = true;
		if (!framed.current) return <View path={path} />;
		return (
			<FieldChrome error={message}>
				<View path={path} />
			</FieldChrome>
		);
	}
	Errored.displayName = `Errored(${View.displayName ?? View.name})`;
	return Errored;
}

/** The entry with focus and bare-control errors added, when it is an input. */
export function withInputChrome(entry: NodeEntry): NodeEntry {
	if (!entry.input) return entry;
	const framed = entry.component && !entry.input.ownsError;
	return {
		...entry,
		component: framed ? withError(entry.component as ComponentType<NodeProps>) : entry.component,
		handlers: { focus: focusHandler, ...entry.handlers },
	};
}
