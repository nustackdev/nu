// ButtonRef -- click trigger. Sends a notify on each click. No value.
//
// Class-level defaults (label, variant, disabled, icon) seed the slice via
// mount props. Server -> tab `write` is a partial merge: missing keys leave
// the slice untouched. When the slice has no label, the path is shown so a
// freshly mounted button stays locatable. Composes the kit Button primitive;
// variant maps to Button variant.
//
// TODO(retune): `icon` prop is a raw string on the wire today. Kit Button
// expects a React node for `leadingIcon`. A lucide-lookup shim in the kit is
// needed to resolve names like "chevron-down" to the icon component; until
// then we render the raw string in a span. Small visual regression on icon
// buttons only; label + click behavior are unaffected.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { Button } from "../../components/ui/button";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

type ButtonVariant = "default" | "secondary" | "ghost" | "destructive";

const VARIANT_TO_KIT: Record<string, ButtonVariant> = {
	primary: "default",
	secondary: "secondary",
	ghost: "ghost",
	danger: "destructive",
};

const factory: SliceFactory = (path, ctx, props) => ({
	type: "ButtonRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	variant: typeof props?.variant === "string" ? (props.variant as string) : "primary",
	disabled: typeof props?.disabled === "boolean" ? (props.disabled as boolean) : false,
	icon: typeof props?.icon === "string" ? (props.icon as string) : null,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			const p = (v ?? {}) as {
				label?: unknown;
				variant?: unknown;
				disabled?: unknown;
				icon?: unknown;
			};
			if ("label" in p) {
				slice.label = p.label == null ? "" : String(p.label);
			}
			if ("variant" in p) {
				slice.variant = p.variant == null ? "primary" : String(p.variant);
			}
			if ("disabled" in p) {
				slice.disabled = Boolean(p.disabled);
			}
			if ("icon" in p) {
				slice.icon = p.icon == null ? null : String(p.icon);
			}
		}),
});

function ButtonView({ path }: { path: string }) {
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const variant = useStore((s) => (s.refs[path]?.variant as string) ?? "primary");
	const disabled = useStore((s) => Boolean(s.refs[path]?.disabled));
	const icon = useStore((s) => (s.refs[path]?.icon as string | null) ?? null);
	const send = useStore((s) => s.send);
	const kitVariant = VARIANT_TO_KIT[variant] ?? "default";
	const text = label === "" ? path : label;
	return (
		<Button
			variant={kitVariant}
			disabled={disabled}
			onClick={() => {
				if (disabled) return;
				send({ op: OP_NOTIFY, ref: path, payload: null });
			}}
		>
			{icon && <span aria-hidden>{icon}</span>}
			{text}
		</Button>
	);
}

export const ButtonRef: RefEntry = { factory, component: ButtonView };
