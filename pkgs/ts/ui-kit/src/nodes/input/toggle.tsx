// ToggleRef -- two-state toolbar button. Browser is source of truth.
//
// Same wire shape as SwitchRef, different renderer: the kit Toggle primitive.
// Pressed or not is the node's `value` (a real bool); a press lands it and
// sends `{event: "change"}` at once (./control.ts). A bare write lands on
// `value` coerced to a bool, a map write merges chrome (label, icon), the
// store answers a read from `value`, and `reset` puts the declared value back.
//
// `icon` is a lucide name, resolved like ButtonRef's, and draws before the
// label. Toggle sizes track IconButton, so a toolbar Row of both lines up,
// and like a button it keeps its size in a Row. With no label the icon name
// is the accessible name.

import { Toggle } from "../../components/ui/toggle";
import { iconFor } from "../../lib/icons";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";
import { asBool, resetHandler, useCommit, useControl, valueWrite } from "./control";

function ToggleView({ path }: NodeProps) {
	const iconName = useStringProp(path, "icon");
	const pressed = useBoolProp(path, "value");
	const c = useControl(path);
	const label = useStringProp(path, "label");
	const { pick } = useCommit(path);
	const Icon = iconFor(iconName);
	const text = label === "" && !Icon ? path.join(" / ") : label;
	return (
		<Toggle
			{...c.aria}
			className="shrink-0"
			size={c.size}
			pressed={pressed}
			disabled={c.disabled}
			autoFocus={c.autoFocus}
			aria-readonly={c.readOnly || undefined}
			aria-label={label === "" && Icon ? iconName : undefined}
			onPressedChange={(next) => {
				if (c.readOnly) return;
				pick(next);
			}}
		>
			{Icon && <Icon aria-hidden />}
			{text}
		</Toggle>
	);
}

export const ToggleRef: NodeEntry = {
	component: ToggleView,
	input: { empty: false },
	handlers: {
		write: valueWrite(asBool),
		reset: resetHandler,
	},
};
