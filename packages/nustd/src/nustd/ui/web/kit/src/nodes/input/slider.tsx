// SliderRef -- numeric slider with min/max/step. Browser is source of truth.
//
// User drags: the node's `value` prop updates immediately (controlled input).
// On commit: notify the server. A server-initiated read is answered by the
// store from `value`. A server-initiated write needs a handler for one reason:
// the scalar form is a bare number and nil has to land as the floor rather
// than as null, or the slider goes uncontrolled and the next read answers
// null. The map form merges {value, min, max, step, label, show_value} the way
// the store merges everything else; those keys are coerced at render.
//
// Composes the kit Slider primitive (Radix Slider) so track/thumb/keyboard
// read through kit tokens. The primitive takes an array value; we wrap our
// scalar accordingly.

import { OPS } from "@nustackdev/ui-core";
import { Slider } from "../../components/ui/slider";
import { Text } from "../../components/ui/text";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useNumberProp,
	useSend,
	useSetValue,
	useStringProp,
} from "../../tree";

function toFiniteNumber(n: unknown, fallback: number): number {
	const v = Number(n);
	return Number.isFinite(v) ? v : fallback;
}

function SliderView({ path }: NodeProps) {
	const min = useNumberProp(path, "min", 0);
	const max = useNumberProp(path, "max", 100);
	const step = useNumberProp(path, "step", 1);
	const value = useNumberProp(path, "value", min);
	const label = useStringProp(path, "label");
	const showValue = useBoolProp(path, "show_value", true);
	const setValue = useSetValue(path);
	const send = useSend(path);

	const commit = () => send(OPS.notify);

	return (
		<div className="flex w-full flex-col gap-1">
			{label && (
				<Text as="span" size="sm" tone="secondary" weight="medium">
					{label}
				</Text>
			)}
			<div className="flex items-center gap-3">
				<Slider
					value={[value]}
					min={min}
					max={max}
					step={step}
					onValueChange={(vals) => setValue(vals[0] ?? 0)}
					onValueCommit={commit}
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
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload && typeof payload === "object" && !Array.isArray(payload)) {
					Object.assign(props, payload);
					if ("value" in payload) {
						props.value = toFiniteNumber(props.value, toFiniteNumber(props.min, 0));
					}
					return;
				}
				props.value = toFiniteNumber(payload, toFiniteNumber(props.min, 0));
			}),
	},
};
