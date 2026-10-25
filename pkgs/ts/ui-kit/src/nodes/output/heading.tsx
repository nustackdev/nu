// HeadingRef -- display-only heading with selectable level (h1..h4) and align.
//
// Server-owned. An object write is a partial merge of {label, level, align,
// size, tone, eyebrow, subtitle} into the node's props, which the default
// store behaviour already does. What it cannot do is the legacy shorthand: a
// bare string payload means `{label: <string>}`, not `value`, and a nil write
// clears the label. That is the one thing this type owns, so it carries a
// `write` handler for it and leaves the object case to the default merge.
// Level and align are normalized at read time. Composes the kit Heading
// primitive: level picks the tag, and the size by default; `size` decouples
// the look from the tag (a `display` hero that is still an h1, a small h2).
// Align takes start / center / end, and left / right as the older spelling.
//
// `eyebrow` is a small accent label above the heading, `subtitle` a secondary
// line under it; either one wraps the heading in a group so all three share
// the align. Its box carries the same 4px of vertical padding as every text
// output (see TextRef, Prose), padding and never margin.

import { Heading } from "../../components/ui/heading";
import { normAlign, TEXT_ALIGN } from "../../lib/align";
import { tone as TONE } from "../../lib/recipes";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	useEnumProp,
	useNumberProp,
	useProp,
	useStringProp,
} from "../../tree";

// Match level to typography ladder from primitives.md §Heading.
const LEVEL_SIZES = {
	1: "3xl",
	2: "2xl",
	3: "xl",
	4: "lg",
} as const;

type HeadingSize = "display" | "3xl" | "2xl" | "xl" | "lg";

const SIZES: readonly HeadingSize[] = ["display", "3xl", "2xl", "xl", "lg"];

// A heading's tones, a subset of the kit's ladder (lib/recipes.ts): never
// muted, which is for labels and hints, and never a status hue.
const TONES = ["primary", "secondary", "accent"] as const;

// A subtitle steps down with the heading it sits under.
const SUBTITLE_SIZES: Record<HeadingSize, string> = {
	display: "text-xl",
	"3xl": "text-xl",
	"2xl": "text-lg",
	xl: "text-base",
	lg: "text-sm",
};

function clampLevel(n: number): 1 | 2 | 3 | 4 {
	if (!Number.isInteger(n)) return 1;
	if (n < 1) return 1;
	if (n > 4) return 4;
	return n as 1 | 2 | 3 | 4;
}

function HeadingView({ path }: NodeProps) {
	const label = useStringProp(path, "label");
	const level = clampLevel(useNumberProp(path, "level", 1));
	const align = TEXT_ALIGN[normAlign(useProp<unknown>(path, "align", "start"))];
	const tone = TONE[useEnumProp(path, "tone", TONES, "primary")];
	const eyebrow = useStringProp(path, "eyebrow");
	const subtitle = useStringProp(path, "subtitle");
	const size = useEnumProp<HeadingSize>(path, "size", SIZES, LEVEL_SIZES[level]);
	const as = `h${level}` as "h1" | "h2" | "h3" | "h4";
	if (eyebrow === "" && subtitle === "") {
		return (
			<Heading as={as} size={size} className={cn("py-1", align, tone)}>
				{label}
			</Heading>
		);
	}
	return (
		<hgroup data-slot="heading-group" className={cn("flex flex-col gap-1 py-1", align)}>
			{eyebrow !== "" ? (
				<p
					data-slot="heading-eyebrow"
					className="font-display text-xs font-semibold uppercase text-accent-text"
				>
					{eyebrow}
				</p>
			) : null}
			<Heading as={as} size={size} className={tone}>
				{label}
			</Heading>
			{subtitle !== "" ? (
				<p
					data-slot="heading-subtitle"
					className={cn("font-display text-text-secondary", SUBTITLE_SIZES[size])}
				>
					{subtitle}
				</p>
			) : null}
		</hgroup>
	);
}

export const HeadingRef: NodeEntry = {
	component: HeadingView,
	fill: true,
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				// Legacy shorthand: a bare string (or nil) maps to {label: ...}.
				if (payload == null || typeof payload !== "object") {
					props.label = payload == null ? "" : String(payload);
					return;
				}
				Object.assign(props, payload as Record<string, unknown>);
			}),
	},
};
