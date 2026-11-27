// IconPickerRef -- icon input whose stored icon string lives in the browser.
//
// The trigger shows the icon (or the placeholder while there is none) and
// opens the kit icon picker (components/ui/icon-picker.tsx): emoji and a
// lucide pack, searched, picked from a grid; a bottom sheet on touch. The
// value is the stored spelling, "lucide:<name>" or "emoji:<char>", "" for
// none. A pick lands it, closes the picker and sends `{event: "change"}` at
// once (./control.ts); "Remove" (when `clearable`) lands "" the same way.
//
// `kinds` picks the tabs and their order ("emoji", "lucide"). A write takes
// a stored value (a bare lucide name reads as "lucide:<name>", `FileText` as
// "lucide:file-text"), "" or nil to clear, or a map that merges chrome; a
// value that is not an icon keeps the icon the node had. `reset` puts the
// declared value back.

import type { NodeHandler } from "@nustackdev/ui-core";
import { useId } from "react";
import { IconPickerField } from "../../components/ui/icon-picker";
import { type IconKind, normalizeIcon } from "../../components/ui/icon-picker-model";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useListProp, useProp, useStringProp } from "../../tree";
import { resetHandler, useCommit, useControl } from "./control";

const KINDS: readonly IconKind[] = ["emoji", "lucide"];

/** The kinds off the wire, known ones only, in order; both when none survive. */
export function toKinds(raw: unknown[]): IconKind[] {
	const out = raw.filter((k): k is IconKind => KINDS.includes(k as IconKind));
	return out.length > 0 ? [...new Set(out)] : [...KINDS];
}

/** A write as a stored icon; "" or nil clears, anything else that is no icon keeps `before`. */
export function toIcon(raw: unknown, before?: unknown): string {
	if (raw == null || (typeof raw === "string" && raw.trim() === "")) return "";
	return normalizeIcon(raw) || normalizeIcon(before);
}

function IconPickerView({ path }: NodeProps) {
	const value = normalizeIcon(useStringProp(path, "value"));
	const rawKinds = useListProp<unknown>(path, "kinds");
	const clearable = useProp<boolean>(path, "clearable", true);
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
				</Text>
			)}
			<IconPickerField
				id={c.id}
				value={value}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled || c.readOnly}
				clearable={clearable !== false}
				placeholder={c.placeholder || undefined}
				kinds={toKinds(rawKinds)}
				triggerProps={{
					autoFocus: c.autoFocus,
					"aria-labelledby": c.label ? `${labelId} ${c.id}` : c.labelledBy,
					"aria-describedby": c.describedBy,
					"aria-required": c.required || undefined,
				}}
				onValueChange={pick}
			/>
		</div>
	);
}

// Not `valueWrite`: a value that is no icon keeps the one the node had, so
// the handler needs the value from before a map merged over it.
const iconWrite: NodeHandler = (ctx, payload) =>
	ctx.update((props) => {
		const before = props.value;
		if (payload && typeof payload === "object" && !Array.isArray(payload)) {
			Object.assign(props, payload);
			if ("value" in payload) props.value = toIcon(props.value, before);
			return;
		}
		props.value = toIcon(payload, before);
	});

export const IconPickerRef: NodeEntry = {
	component: IconPickerView,
	input: { empty: "" },
	handlers: {
		write: iconWrite,
		reset: resetHandler,
	},
};
