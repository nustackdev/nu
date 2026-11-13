// SegmentedControlRef -- single choice as a joined row of buttons. Browser is
// source of truth.
//
// Same state shape as RadioGroupRef, a different affordance: the picked
// option's value is the node's `value` ("" for none), a pick lands it and
// sends `{event: "change"}` at once (./control.ts). Arrow keys move the pick
// (radiogroup semantics, from the kit primitive). A bare write selects (nil
// clears), an object payload merges into props (how `options` is replaced),
// the store answers a read from `value`, and `reset` puts the declared value
// back.
//
// The group is named by its label (`aria-labelledby`), or by the Field
// around it. `fill` stretches the track over the width it is given, the
// segments sharing it. Composes the kit SegmentedControl primitive.

import { useId, useMemo } from "react";
import { SegmentedControl, SegmentedControlItem } from "../../components/ui/segmented-control";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useStringProp,
} from "../../tree";
import { asText, resetHandler, useCommit, useControl, valueWrite } from "./control";
import { normalizeOptions } from "./select";

function SegmentedControlView({ path }: NodeProps) {
	const selected = useStringProp(path, "value");
	const fill = useBoolProp(path, "fill");
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
			<SegmentedControl
				id={c.id}
				value={selected}
				size={c.size}
				fill={fill}
				invalid={c.invalid}
				disabled={c.disabled}
				required={c.required}
				aria-labelledby={c.label ? labelId : c.labelledBy}
				aria-describedby={c.describedBy}
				aria-readonly={c.readOnly || undefined}
				onValueChange={(next) => {
					if (!c.readOnly) pick(next);
				}}
				className={fill ? undefined : "self-start"}
			>
				{options.map((o, i) => (
					<SegmentedControlItem
						key={o.value}
						value={o.value}
						autoFocus={c.autoFocus && (selected ? o.value === selected : i === 0)}
					>
						{o.label}
					</SegmentedControlItem>
				))}
			</SegmentedControl>
		</div>
	);
}

export const SegmentedControlRef: NodeEntry = {
	component: SegmentedControlView,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
