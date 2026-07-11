// ButtonRef -- click trigger. Sends a notify on each click. No value.
//
// Class-level defaults (label, variant, disabled, icon) seed the slice via
// mount props. Server -> tab `write` is a partial merge: missing keys leave
// the slice untouched. When the slice has no label, the path is shown so a
// freshly mounted button stays locatable.

import { OP_NOTIFY } from "@nustackdev/ui-core";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const VARIANT_CLASSES: Record<string, string> = {
	primary: "bg-primary text-primary-foreground hover:opacity-90",
	secondary: "bg-secondary text-secondary-foreground hover:opacity-90",
	ghost: "bg-transparent text-foreground hover:bg-muted",
	danger: "bg-red-600 text-white hover:bg-red-700",
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
	const cls = VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.primary;
	const text = label === "" ? path : label;
	return (
		<button
			type="button"
			disabled={disabled}
			className={`rounded px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50 ${cls}`}
			onClick={() => {
				if (disabled) return;
				send({ op: OP_NOTIFY, ref: path, payload: null });
			}}
		>
			{icon && <span className="mr-1">{icon}</span>}
			{text}
		</button>
	);
}

export const ButtonRef: RefEntry = { factory, component: ButtonView };
