// ButtonRef -- click trigger. Sends a notify on each click. No value.
//
// Chrome (label, variant, disabled, icon) is props, seeded at the slot and
// merged by any later write, which is the default store behaviour, so there
// is no handler here. When the node has no label the path is shown, so a
// button that just appeared stays locatable. Composes the kit Button
// primitive; variant maps to a Button variant.
//
// TODO(retune): `icon` is a raw string on the wire. Kit Button expects a
// React node for `leadingIcon`. A lucide-lookup shim is needed to resolve
// names like "chevron-down"; until then the raw string renders in a span.

import { OPS } from "@nustackdev/ui-core";
import { Button } from "../../components/ui/button";
import { type NodeEntry, type NodeProps, useBoolProp, useSend, useStringProp } from "../../tree";

type ButtonVariant = "default" | "secondary" | "ghost" | "destructive";

const VARIANT_TO_KIT: Record<string, ButtonVariant> = {
	primary: "default",
	secondary: "secondary",
	ghost: "ghost",
	danger: "destructive",
};

function ButtonView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const variant = useStringProp(path, "variant", "primary");
	const disabled = useBoolProp(path, "disabled");
	const icon = useStringProp(path, "icon");
	const send = useSend(path);
	const kitVariant = VARIANT_TO_KIT[variant] ?? "default";
	const text = label === "" ? path.join(" / ") : label;
	return (
		<Button
			variant={kitVariant}
			disabled={disabled}
			onClick={() => {
				if (disabled) return;
				send(OPS.notify);
			}}
		>
			{icon && <span aria-hidden>{icon}</span>}
			{text}
		</Button>
	);
}

export const ButtonRef: NodeEntry = { component: ButtonView };
