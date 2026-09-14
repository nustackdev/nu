// SwitchRef -- boolean toggle (switch affordance). Browser is source of truth.
//
// Same wire shape as CheckboxRef, different renderer: kit Switch primitive.
// User toggles: the node's `checked` prop flips immediately (local edit), a
// notify ships to the server. State lives on `checked`, not on `value`, so a
// write handler lands the payload there (coerced to a real bool, the input
// must never go uncontrolled) and a read handler answers with it.

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { Switch } from "../../components/ui/switch";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

function SwitchView({ path }: NodeProps) {
	const checked = useBoolProp(path, "checked");
	const label = useStringProp(path, "label");
	const setProps = useSetProps(path);
	const send = useSend(path);
	const id = useId();
	return (
		<div className="inline-flex items-center gap-2">
			<Switch
				id={id}
				checked={checked}
				onCheckedChange={(next) => {
					setProps({ checked: next });
					send(OPS.notify);
				}}
			/>
			{label && (
				<label htmlFor={id} className="text-base text-text-primary cursor-pointer">
					{label}
				</label>
			)}
		</div>
	);
}

export const SwitchRef: NodeEntry = {
	component: SwitchView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				props.checked = Boolean(payload);
			}),
		read: (ctx) => ctx.send(OPS.read, Boolean(ctx.node.props.checked), ctx.frame.id),
	},
};
