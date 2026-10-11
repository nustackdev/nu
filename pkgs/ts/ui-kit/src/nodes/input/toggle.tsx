// ToggleRef -- two-state toolbar button. Browser is source of truth.
//
// Same wire shape as SwitchRef, different renderer and prop: the kit Toggle
// primitive, state on `pressed`. User presses: `pressed` flips immediately
// (local edit), a notify ships to the server. A bare write lands on
// `pressed` (coerced to a real bool, the toggle must never go uncontrolled),
// a map write merges chrome (label, icon), and a read answers with `pressed`.
//
// `icon` resolves through ./icons like ButtonRef's and draws before the
// label. Toggle sizes track IconButton, so a toolbar Row of both lines up,
// and like a button it keeps its size in a Row. With no label the icon name
// is the accessible name.

import { OPS } from "@nustackdev/ui-core";
import { Toggle } from "../../components/ui/toggle";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";
import { iconFor } from "./icons";

function ToggleView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const iconName = useStringProp(path, "icon");
	const pressed = useBoolProp(path, "pressed");
	const setProps = useSetProps(path);
	const send = useSend(path);
	const Icon = iconFor(iconName);
	const text = label === "" && !Icon ? path.join(" / ") : label;
	return (
		<Toggle
			className="shrink-0"
			pressed={pressed}
			aria-label={label === "" && Icon ? iconName : undefined}
			onPressedChange={(next) => {
				setProps({ pressed: next });
				send(OPS.notify);
			}}
		>
			{Icon && <Icon aria-hidden />}
			{text}
		</Toggle>
	);
}

export const ToggleRef: NodeEntry = {
	component: ToggleView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload && typeof payload === "object" && !Array.isArray(payload)) {
					Object.assign(props, payload);
					return;
				}
				props.pressed = Boolean(payload);
			}),
		read: (ctx) => ctx.send(OPS.read, Boolean(ctx.node.props.pressed), ctx.frame.id),
	},
};
