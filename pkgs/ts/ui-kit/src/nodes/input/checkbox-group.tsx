// CheckboxGroupRef -- multi choice as a list of checkboxes. Browser is source
// of truth.
//
// The ticked option values are the node's `value`, a list in option order
// ([] for none). Each tick lands the list and sends `{event: "change"}` at
// once (./control.ts). A write of a list replaces it (items stringified), a
// lone string ticks just that one, nil clears, and an object payload merges
// into props (how `options` is replaced). The store answers a read from
// `value`, and `reset` puts the declared list back.
//
// The group is named by its label (`aria-labelledby`), or by the Field
// around it. Options arrive raw off the wire (strings or {value,label} maps)
// and are normalized at render. Composes the kit CheckboxGroup primitive.

import { useId, useMemo } from "react";
import { CheckboxGroup } from "../../components/ui/checkbox-group";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useListProp, useStringProp } from "../../tree";
import { resetHandler, useCommit, useControl, valueWrite } from "./control";
import { normalizeOptions } from "./select";

/** A list value: a list stringified item by item, a lone string as one item, anything else empty. */
export const asList = (raw: unknown): string[] => {
	if (Array.isArray(raw)) return raw.filter((x) => x != null).map(String);
	if (typeof raw === "string" && raw !== "") return [raw];
	return [];
};

function CheckboxGroupView({ path }: NodeProps) {
	const picked = useListProp<string>(path, "value");
	const orientation = useStringProp(path, "orientation", "vertical");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const c = useControl(path);
	const { pick } = useCommit(path);
	const labelId = useId();
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Text
					as="span"
					id={labelId}
					size="sm"
					tone="secondary"
					weight="medium"
					className={c.disabled ? "opacity-50" : undefined}
				>
					{c.label}
					{c.required ? (
						<span className="ml-0.5 text-accent-text" aria-hidden>
							*
						</span>
					) : null}
				</Text>
			)}
			<CheckboxGroup
				id={c.id}
				options={options}
				value={picked}
				orientation={orientation === "horizontal" ? "horizontal" : "vertical"}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled}
				readOnly={c.readOnly}
				autoFocus={c.autoFocus}
				aria-labelledby={c.label ? labelId : c.labelledBy}
				aria-describedby={c.describedBy}
				onValueChange={pick}
			/>
		</div>
	);
}

export const CheckboxGroupRef: NodeEntry = {
	component: CheckboxGroupView,
	input: { empty: [] },
	handlers: {
		write: valueWrite(asList),
		reset: resetHandler,
	},
};
