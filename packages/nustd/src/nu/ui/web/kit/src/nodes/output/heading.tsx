// HeadingRef -- display-only heading with selectable level (h1..h4) and align.
//
// Server-owned. An object write is a partial merge of {label, level, align}
// into the node's props, which the default store behaviour already does.
// What it cannot do is the legacy shorthand: a bare string payload means
// `{label: <string>}`, not `value`, and a nil write clears the label. That is
// the one thing this type owns, so it carries a `write` handler for it and
// leaves the object case to the default merge. Level and align are normalized
// at read time. Composes the kit Heading primitive: level maps to size, align
// to text-align utility.

import { Heading } from "../../components/ui/heading";
import { type NodeEntry, type NodeProps, useNumberProp, useStringProp } from "../../tree";

// Match level to typography ladder from primitives.md §Heading.
const LEVEL_SIZES = {
	1: "3xl",
	2: "2xl",
	3: "xl",
	4: "lg",
} as const;

const ALIGN_CLASSES: Record<string, string> = {
	left: "text-left",
	center: "text-center",
	right: "text-right",
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
	const align = useStringProp(path, "align", "left");
	const size = LEVEL_SIZES[level] ?? LEVEL_SIZES[1];
	const alignCls = ALIGN_CLASSES[align] ?? ALIGN_CLASSES.left;
	const as = `h${level}` as "h1" | "h2" | "h3" | "h4";
	return (
		<Heading as={as} size={size} className={alignCls}>
			{label}
		</Heading>
	);
}

export const HeadingRef: NodeEntry = {
	component: HeadingView,
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
