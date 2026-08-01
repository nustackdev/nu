// SwitchRef -- boolean toggle (switch affordance). Browser is source of truth.
//
// Same wire shape as CheckboxRef, different renderer: kit Switch primitive.
// User toggles: local store flips immediately, notify ships to server.
// Server-initiated read: answer with current checked value.
// Server-initiated write: replace the checked value (canonical / reset).
// Class-level defaults (label, checked) seed the slice via mount props.

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { Switch } from "../../components/ui/switch";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

const factory: SliceFactory = (path, ctx, props) => ({
	type: "SwitchRef",
	value: null,
	label: typeof props?.label === "string" ? (props.label as string) : "",
	checked: typeof props?.checked === "boolean" ? (props.checked as boolean) : false,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			// Non-bool / nil payload coerces to a real bool; the input must
			// never go uncontrolled.
			slice.checked = Boolean(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return Boolean(slice?.checked);
	},
});

function SwitchView({ path }: { path: string }) {
	const checked = useStore((s) => Boolean(s.refs[path]?.checked));
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const send = useStore((s) => s.send);
	const id = useId();
	return (
		<div className="inline-flex items-center gap-2">
			<Switch
				id={id}
				checked={checked}
				onCheckedChange={(next) => {
					useStore.setState((draft) => {
						const slice = draft.refs[path];
						if (slice) slice.checked = next;
					});
					send({ op: OP_NOTIFY, ref: path, payload: null });
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

export const SwitchRef: RefEntry = { factory, component: SwitchView };
