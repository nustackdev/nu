// RadioGroupRef -- single-choice radio group. Browser is source of truth.
//
// Same state shape as SelectRef, different affordance. User picks: the node's
// `selected` prop updates immediately (local edit), a notify ships to the
// server. State lives on `selected`, not on `value`, so a bare write has to be
// steered there by a handler; an object payload merges into props the way the
// store merges everything else, which is how `options` gets replaced. A read
// answers with `selected`.
//
// Options arrive raw off the wire (strings or {value,label} maps) and are
// normalized at render rather than in a factory. Composes the kit RadioGroup
// primitive.

import { OPS } from "@nustackdev/ui-core";
import { useMemo } from "react";
import { RadioGroup, RadioGroupItem } from "../../components/ui/radio-group";
import {
	type NodeEntry,
	type NodeProps,
	useListProp,
	useSend,
	useSetProps,
	useStringProp,
} from "../../tree";

type Option = { value: string; label: string };

function normalizeOptions(raw: unknown[]): Option[] {
	const out: Option[] = [];
	for (const item of raw) {
		if (typeof item === "string") {
			out.push({ value: item, label: item });
		} else if (item && typeof item === "object") {
			const o = item as { value?: unknown; label?: unknown };
			const value = o.value == null ? "" : String(o.value);
			const label = o.label == null ? value : String(o.label);
			out.push({ value, label });
		}
	}
	return out;
}

function RadioGroupView({ path }: NodeProps) {
	const selected = useStringProp(path, "selected");
	const orientation = useStringProp(path, "orientation", "vertical");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const setProps = useSetProps(path);
	const send = useSend(path);
	const listCls =
		orientation === "horizontal" ? "flex flex-row flex-wrap gap-4" : "flex flex-col gap-2";
	const prefix = path.join("-");
	return (
		<RadioGroup
			value={selected}
			onValueChange={(next) => {
				setProps({ selected: next });
				send(OPS.notify);
			}}
			className={listCls}
		>
			{options.map((o) => {
				const id = `radio-${prefix}-${o.value}`;
				return (
					<div key={o.value} className="flex items-center gap-2">
						<RadioGroupItem value={o.value} id={id} />
						<label htmlFor={id} className="text-base text-text-primary cursor-pointer">
							{o.label}
						</label>
					</div>
				);
			})}
		</RadioGroup>
	);
}

export const RadioGroupRef: NodeEntry = {
	component: RadioGroupView,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				// Map form merges (that is how `options` is pushed). Bare value
				// push (string or coercible) selects; nil clears the selection.
				if (payload && typeof payload === "object" && !Array.isArray(payload)) {
					Object.assign(props, payload);
					return;
				}
				props.selected = payload == null ? "" : String(payload);
			}),
		read: (ctx) => ctx.send(OPS.read, String(ctx.node.props.selected ?? ""), ctx.frame.id),
	},
};
