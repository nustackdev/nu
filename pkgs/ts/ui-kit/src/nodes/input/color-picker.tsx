// ColorPickerRef -- color input whose `#rrggbb` value lives in the browser.
//
// The trigger shows the swatch and the hex; it opens a popover with the
// saturation/brightness area, a hue slider, a hex field and the optional
// swatches. A drag in the area or on the hue is a local edit, the release
// commits; a swatch lands and commits at once; the hex field edits as a full
// hex is typed and commits on blur. `{event: "change"}` only when the color
// moved (./control.ts). Enter in the hex field, or on the closed trigger,
// submits (and asks an enclosing Form to submit); Space opens the popover.
//
// `swatches` is a list of hex strings, or "palette" for the kit chart palette
// (read off the theme tokens, see components/ui/color-picker.tsx). A write
// takes a hex (`#abc` widens to `#aabbcc`, case folds) or a map that merges
// chrome; anything that is not a hex keeps the color it had. `reset` puts
// the declared value back.

import type { NodeHandler } from "@nustackdev/ui-core";
import { useId } from "react";
import { ColorPicker, normalizeHex } from "../../components/ui/color-picker";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useProp, useStringProp } from "../../tree";
import { isEnter, resetHandler, useCommit, useControl } from "./control";

const BLACK = "#000000";

/** A write as `#rrggbb`; a non-hex keeps the color the node had. */
export function toHex(raw: unknown, before?: unknown): string {
	return normalizeHex(raw) ?? normalizeHex(before) ?? BLACK;
}

function ColorPickerView({ path }: NodeProps) {
	const value = normalizeHex(useStringProp(path, "value")) ?? BLACK;
	const swatches = useProp<unknown>(path, "swatches", null);
	const showHex = useProp<boolean>(path, "show_hex", true);
	const c = useControl(path);
	const { edit, commit, submit } = useCommit(path);
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
				</Text>
			)}
			<ColorPicker
				id={c.id}
				value={value}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled || c.readOnly}
				showHex={showHex !== false}
				swatches={
					swatches === "palette"
						? "palette"
						: Array.isArray(swatches)
							? swatches.map(String)
							: undefined
				}
				triggerProps={{
					autoFocus: c.autoFocus,
					"aria-labelledby": c.label ? `${labelId} ${c.id}` : c.labelledBy,
					"aria-describedby": c.describedBy,
					"aria-required": c.required || undefined,
					onKeyDown: (e) => {
						if (!isEnter(e)) return;
						e.preventDefault();
						submit(e.currentTarget);
					},
				}}
				onValueChange={edit}
				onValueCommit={(v) => {
					// Radix reports a key's commit before its move: land the value first.
					edit(v);
					commit();
				}}
				onEnter={(trigger) => submit(trigger)}
			/>
		</div>
	);
}

// Not `valueWrite`: a bad hex keeps the color the node had, so the handler
// needs the value from before a map merged over it.
const hexWrite: NodeHandler = (ctx, payload) =>
	ctx.update((props) => {
		const before = props.value;
		if (payload && typeof payload === "object" && !Array.isArray(payload)) {
			Object.assign(props, payload);
			if ("value" in payload) props.value = toHex(props.value, before);
			return;
		}
		props.value = toHex(payload, before);
	});

export const ColorPickerRef: NodeEntry = {
	component: ColorPickerView,
	fill: true,
	input: { empty: BLACK },
	handlers: {
		write: hexWrite,
		reset: resetHandler,
	},
};
