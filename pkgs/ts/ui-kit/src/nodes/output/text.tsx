// TextRef -- display-only paragraph string. Renders via kit Text primitive.
//
// Server-owned, and there is nothing to do on a write: the default store
// behaviour lands a bare payload on `value` and merges an object one into the
// props (`{tone: "muted"}`), so this type is a component and nothing else.
// Nil payload (Nu sentinel) reads back as the empty string at render time.
// Wire strings often carry `\n`; whitespace is preserved here.
//
// Style props are the Text primitive's own variants: `tone`, `size`,
// `weight`, `mono`, plus `align` and `lines`. An unknown value reads as the
// default. `lines` clamps the paragraph: 0 wraps freely, 1 is a single line
// with an ellipsis, more is a line clamp. A text keeps its own width in a
// block flow, so a centered or end-aligned one takes the full row instead,
// or there would be no room to align it in.
//
// Its box carries the same 4px of vertical padding as Prose, so every text
// output has one edge: padding, never margin, so it cannot collapse or leak.
//
// In a Line (inline flow) it is one run of the sentence: a span with no
// padding of its own, taking the Line's type and white-space, so it wraps
// mid-run beside the badges and links around it and its newlines fold into
// word spaces like any paragraph's. Only the style props that were set ride
// on the span (a muted or mono run), so the rest stays the Line's.

import type { CSSProperties } from "react";
import { Text, textVariants } from "../../components/ui/text";
import { normAlign, TEXT_ALIGN } from "../../lib/align";
import { TONES } from "../../lib/recipes";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useEnumProp,
	useFlow,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";

const SIZES = ["xs", "sm", "base", "lg", "xl"] as const;
const WEIGHTS = ["regular", "medium", "semibold", "bold"] as const;

/** Class and style that clamp a block to `lines` lines; nothing for 0. */
export function clampLines(lines: number): { className?: string; style?: CSSProperties } {
	if (!Number.isInteger(lines) || lines <= 0) return {};
	if (lines === 1)
		return { className: "max-w-full overflow-hidden text-ellipsis whitespace-nowrap" };
	return {
		className: "overflow-hidden max-w-full",
		style: { display: "-webkit-box", WebkitBoxOrient: "vertical", WebkitLineClamp: lines },
	};
}

function TextView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	const align = normAlign(useProp<unknown>(path, "align", "start"));
	const mono = useBoolProp(path, "mono");
	const lines = useNumberProp(path, "lines", 0);
	const tone = useEnumProp(path, "tone", TONES, "primary");
	const size = useEnumProp(path, "size", SIZES, "base");
	const weight = useEnumProp(path, "weight", WEIGHTS, "regular");
	if (useFlow() === "inline") {
		// null drops a variant entirely, so an unset prop adds no class.
		const runCls = cn(
			textVariants({
				size: null,
				tone: tone === "primary" ? null : tone,
				weight: weight === "regular" ? null : weight,
				mono: mono ? true : null,
			}),
		);
		return (
			<span data-slot="text" className={runCls || undefined}>
				{value}
			</span>
		);
	}
	const clamp = clampLines(lines);
	return (
		<Text
			as="p"
			size={size}
			tone={tone}
			weight={weight}
			mono={mono}
			className={cn(
				"py-1",
				lines === 1 ? undefined : "whitespace-pre-wrap",
				TEXT_ALIGN[align],
				align !== "start" && "w-full",
				clamp.className,
			)}
			style={clamp.style}
		>
			{value}
		</Text>
	);
}

export const TextRef: NodeEntry = { component: TextView };
