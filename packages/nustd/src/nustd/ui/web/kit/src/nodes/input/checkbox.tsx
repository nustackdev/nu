// CheckboxRef -- boolean toggle. Browser is source of truth.
//
// User toggles: the node's `checked` prop flips immediately (local edit), a
// notify ships to the server. Its state does not live on `value`, it lives on
// `checked`, so both directions need a handler: a write must land the payload
// on `checked` (coerced to a real bool, the input must never go uncontrolled)
// and a read must answer with `checked` rather than `props.value`.
//
// Chrome (label, checked) is just more props, declared at the slot and read at
// render. Composes the kit Checkbox primitive (Radix under the hood).

import { OPS } from "@nustackdev/ui-core";
import { useId } from "react";
import { Checkbox } from "../../components/ui/checkbox";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

function CheckboxView({ path }: NodeProps) {
	const checked = useBoolProp(path, "checked");
	const label = useStringProp(path, "label");
	const setProps = useSetProps(path);
	const send = useSend(path);
	const id = useId();
	return (
		<div className="inline-flex items-center gap-2">
			<Checkbox
				id={id}
				checked={checked}
				onCheckedChange={(next) => {
					setProps({ checked: next === true });
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

export const CheckboxRef: NodeEntry = {
	component: CheckboxView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				props.checked = Boolean(payload);
			}),
		read: (ctx) => ctx.send(OPS.read, Boolean(ctx.node.props.checked), ctx.frame.id),
	},
};
