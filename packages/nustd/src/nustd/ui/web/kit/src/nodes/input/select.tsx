// SelectRef -- single-select dropdown. Browser is source of truth.
//
// User picks: the node's `selected` prop updates immediately (local edit), a
// notify ships to the server. State lives on `selected`, not on `value`, so a
// bare write has to be steered there by a handler; an object payload merges
// into props the way the store merges everything else, which is how `options`
// gets replaced. A read answers with `selected`.
//
// Options arrive raw off the wire (strings or {value,label} maps) and are
// normalized at render rather than in a factory. Composes the kit Select
// primitive (Radix Select) so the popover reads through tokens on both
// themes; native <select> is dropped.

import { OPS } from "@nustackdev/ui-core";
import { useId, useMemo } from "react";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "../../components/ui/select";
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

function SelectView({ path }: NodeProps) {
	const selected = useStringProp(path, "selected");
	const label = useStringProp(path, "label");
	const placeholder = useStringProp(path, "placeholder");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const setProps = useSetProps(path);
	const send = useSend(path);
	const id = useId();
	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<Select
				value={selected || undefined}
				onValueChange={(next) => {
					setProps({ selected: next });
					send(OPS.notify);
				}}
			>
				<SelectTrigger id={id}>
					<SelectValue placeholder={placeholder} />
				</SelectTrigger>
				<SelectContent>
					{options.map((o) => (
						<SelectItem key={o.value} value={o.value}>
							{o.label}
						</SelectItem>
					))}
				</SelectContent>
			</Select>
		</div>
	);
}

export const SelectRef: NodeEntry = {
	component: SelectView,
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
