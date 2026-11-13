// RangeSliderRef -- two-thumb slider whose `[low, high]` lives in the browser.
//
// Same commit path as SliderRef (./slider.tsx): dragging is a local edit, the
// release or an arrow key commits, `{event: "change"}` only when the pair
// moved (./control.ts). A write takes a bare pair, or a map that merges
// {value, min, max, step, marks, format, label, ...}; anything that is not a
// pair of numbers lands as `[min, max]`, and a pair is clamped and put in
// order, so the control never sees a stray shape. `reset` puts the declared
// pair back; a Form gathers it as a two-item list.
//
// a11y: the root is a group named by the label (its own, or the Field's) and
// each thumb has its own name, `thumb_labels` ("Minimum", "Maximum"). The
// Field's describedby and invalid land on both thumbs. Composes the kit
// RangeSlider (kit Slider + readout + marks).

import type { Props } from "@nustackdev/ui-core";
import { useId } from "react";
import {
	RangeSlider,
	type SliderMark,
	type SliderRange,
	stepDecimals,
} from "../../components/ui/range-slider";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";
import { resetHandler, useCommit, useControl, valueWrite } from "./control";

function finite(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

function bounds(props: Props): SliderRange {
	return [finite(props.min, 0), finite(props.max, 100)];
}

const fullRange = (props: Props): SliderRange => bounds(props);

/** Any write as an ordered pair inside `[min, max]`; `[min, max]` when it is not a pair. */
export function toRange(raw: unknown, props: Props): SliderRange {
	const [lo, hi] = bounds(props);
	if (!Array.isArray(raw) || raw.length !== 2) return [lo, hi];
	const a = Math.min(hi, Math.max(lo, finite(raw[0], lo)));
	const b = Math.min(hi, Math.max(lo, finite(raw[1], hi)));
	return a <= b ? [a, b] : [b, a];
}

/** `"{}%"` style template: `{}` is the number, rounded to the step. */
function formatter(template: string, decimals: number): (n: number) => string {
	return (n) => {
		const s = n.toFixed(decimals);
		return template.includes("{}") ? template.replaceAll("{}", s) : s;
	};
}

function marksOf(raw: unknown[]): SliderMark[] {
	const out: SliderMark[] = [];
	for (const m of raw) {
		if (typeof m === "number") out.push({ value: m });
		else if (m && typeof m === "object" && Number.isFinite(Number((m as SliderMark).value))) {
			const { value, label } = m as SliderMark;
			out.push({ value: Number(value), label: label == null ? undefined : String(label) });
		}
	}
	return out;
}

function RangeSliderView({ path }: NodeProps) {
	const min = useNumberProp(path, "min", 0);
	const max = useNumberProp(path, "max", 100);
	const step = useNumberProp(path, "step", 1);
	const raw = useProp<unknown>(path, "value", null);
	const value = toRange(raw, { min, max });
	const showValue = useBoolProp(path, "show_value", true);
	const format = useStringProp(path, "format", "{}");
	const marks = marksOf(useListProp<unknown>(path, "marks"));
	const names = useListProp<string>(path, "thumb_labels");
	const c = useControl(path);
	const { edit, commit } = useCommit(path);
	const labelId = useId();
	const fmt = formatter(format, stepDecimals(step));

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
			<RangeSlider
				id={c.id}
				aria-labelledby={c.label ? labelId : c.labelledBy}
				aria-describedby={c.describedBy}
				value={value}
				min={min}
				max={max}
				step={step}
				size={c.size}
				disabled={c.disabled || c.readOnly}
				thumbLabels={[names[0] || "Minimum", names[1] || "Maximum"]}
				thumbProps={{
					autoFocus: c.autoFocus,
					"aria-describedby": c.describedBy,
					"aria-invalid": c.invalid || undefined,
					"aria-required": c.required || undefined,
				}}
				marks={marks}
				formatValue={fmt}
				showValue={showValue}
				onValueChange={edit}
				onValueCommit={(v) => {
					// Radix reports a key's commit before its move: land the value first.
					edit(v);
					commit();
				}}
			/>
		</div>
	);
}

export const RangeSliderRef: NodeEntry = {
	component: RangeSliderView,
	fill: true,
	input: { empty: fullRange },
	handlers: {
		write: valueWrite(toRange),
		reset: resetHandler,
	},
};
