// RadioGroupRef -- single-choice radio group. Browser is source of truth.
//
// Same state shape as SelectRef, different affordance. The picked option's
// value is the node's `value` (null for none); a pick lands it and sends
// `{event: "change"}` at once (./control.ts). A bare write selects (nil or
// "" clears), an object payload merges into props (how `options` is replaced),
// the store answers a read from `value`, and `reset` puts the declared value
// back.
//
// The group is named by its label (`aria-labelledby`), or by the Field
// around it. Options arrive raw off the wire (strings or {value,label} maps)
// and are normalized at render. Composes the kit RadioGroup primitive.

import { useId, useMemo } from "react";
import { Label } from "../../components/ui/field";
import { RadioGroup, RadioGroupItem } from "../../components/ui/radio-group";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useListProp, useStringProp } from "../../tree";
import { asTextOrNull, resetHandler, useCommit, useControl, valueWrite } from "./control";
import { normalizeOptions } from "./select";

function RadioGroupView({ path }: NodeProps) {
	const selected = useStringProp(path, "value");
	const orientation = useStringProp(path, "orientation", "vertical");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const c = useControl(path);
	const { pick } = useCommit(path);
	const labelId = useId();
	const listCls =
		orientation === "horizontal" ? "flex flex-row flex-wrap gap-4" : "flex flex-col gap-2";
	const prefix = `${c.id}-opt`;
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
			<RadioGroup
				id={c.id}
				value={selected}
				orientation={orientation === "horizontal" ? "horizontal" : "vertical"}
				disabled={c.disabled}
				required={c.required}
				aria-labelledby={c.label ? labelId : c.labelledBy}
				aria-describedby={c.describedBy}
				aria-invalid={c.invalid || undefined}
				aria-readonly={c.readOnly || undefined}
				onValueChange={(next) => {
					if (!c.readOnly) pick(next);
				}}
				className={listCls}
			>
				{options.map((o, i) => {
					const id = `${prefix}-${i}`;
					return (
						<div key={o.value} className="flex items-center gap-2">
							<RadioGroupItem
								value={o.value}
								id={id}
								size={c.size}
								invalid={c.invalid}
								autoFocus={c.autoFocus && i === 0}
							/>
							<Label htmlFor={id} inline disabled={c.disabled}>
								{o.label}
							</Label>
						</div>
					);
				})}
			</RadioGroup>
		</div>
	);
}

export const RadioGroupRef: NodeEntry = {
	component: RadioGroupView,
	input: { empty: null },
	handlers: {
		write: valueWrite(asTextOrNull),
		reset: resetHandler,
	},
};
