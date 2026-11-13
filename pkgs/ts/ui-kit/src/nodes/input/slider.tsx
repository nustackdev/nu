// SliderRef -- numeric slider with min/max/step. Browser is source of truth.
//
// Dragging is a local edit (the node's `value` follows the thumb). The
// release, or an arrow key, commits: `{event: "change"}` when the value moved
// (./control.ts). A server-initiated write needs a handler: the scalar form
// is a bare number and nil lands on the floor rather than as null, or the
// slider goes uncontrolled and the next read answers null. The map form
// merges {value, min, max, step, label, show_value, ...}. `reset` puts the
// declared value back.
//
// The thumb (the element with `role="slider"`) carries the id, the label and
// the Field's aria. Composes the kit Slider primitive (Radix Slider); the
// primitive takes an array value, so the scalar is wrapped.

import { useId } from "react";
import { Slider } from "../../components/ui/slider";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useBoolProp, useNumberProp } from "../../tree";
import { resetHandler, useCommit, useControl, valueWrite } from "./control";

function toFiniteNumber(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

const floorOf = (props: Record<string, unknown>) => toFiniteNumber(props.min, 0);

function SliderView({ path }: NodeProps) {
	const min = useNumberProp(path, "min", 0);
	const max = useNumberProp(path, "max", 100);
	const step = useNumberProp(path, "step", 1);
	const value = useNumberProp(path, "value", min);
	const showValue = useBoolProp(path, "show_value", true);
	const c = useControl(path);
	const { edit, commit } = useCommit(path);
	const labelId = useId();

	return (
		<div className="flex w-full flex-col gap-1">
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
				</Text>
			)}
			<div className="flex items-center gap-3">
				<Slider
					value={[value]}
					min={min}
					max={max}
					step={step}
					size={c.size}
					disabled={c.disabled || c.readOnly}
					thumbProps={{
						...c.aria,
						autoFocus: c.autoFocus,
						"aria-labelledby": c.label ? labelId : c.labelledBy,
					}}
					onValueChange={(vals) => edit(vals[0] ?? min)}
					// Radix fires a key's commit before its change, so the commit
					// lands the value it carries first, or a key press would report
					// the step before it.
					onValueCommit={(vals) => {
						edit(vals[0] ?? min);
						commit();
					}}
					className="flex-1"
				/>
				{showValue && (
					<Text as="span" size="sm" tone="primary" mono className="tabular-nums shrink-0">
						{value}
					</Text>
				)}
			</div>
		</div>
	);
}

export const SliderRef: NodeEntry = {
	component: SliderView,
	fill: true,
	input: { empty: floorOf },
	handlers: {
		write: valueWrite((raw, props) => toFiniteNumber(raw, floorOf(props))),
		reset: resetHandler,
	},
};
