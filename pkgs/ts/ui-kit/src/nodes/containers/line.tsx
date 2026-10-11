// Line -- children inline, wrapping like a paragraph. Draws its children in
// the kit Line primitive and hands them an "inline" flow. Each child is led
// by one word space (`LineCell`), which collapses at the start of a line, so
// runs break between items and a wrapped line never starts indented. A text
// run that opens with punctuation or a space gets none, so ", press" sits
// right after the run before it.
//
// The content leaves read that flow and draw as runs of the sentence: a
// TextRef is a span with no block padding, a LinkRef an inline anchor, a
// Badge, Kbd, Shortcut or StatusDot a chip on the text's baseline. The same
// leaves outside a Line draw as they always have.
//
// A block leaf in a Line (a chart, Markdown, an Alert, a Heading) is not a
// run: it breaks the line, drawn on its own between the runs before and
// after it. Put those in a Column next to the Line instead.
//
// Chrome is plain props, merged by the default store `write`: `align`
// (start, center, end) and `wrap` (false keeps one line and clips the end).
// `fill`: a Line is a paragraph, it takes the width it is given and wraps
// in it, so in a Row it shares the free width instead of sizing to its runs.

import { Line as LinePrimitive } from "../../components/ui/line";
import {
	type CellProps,
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useNode,
	useProp,
	useStringProp,
} from "../../tree";

// Starts with a space or closing punctuation: no word space before it.
const NO_SPACE_BEFORE = /^[\s.,;:!?)\]}%'"’”…]/;

function LineCell({ path, children }: CellProps) {
	const { type, props } = useNode(path);
	const value = type === "TextRef" && typeof props.value === "string" ? props.value : "";
	return (
		<>
			{NO_SPACE_BEFORE.test(value) ? null : " "}
			{children}
		</>
	);
}

const ALIGNS = new Set(["start", "center", "end"] as const);
type Align = "start" | "center" | "end";

function LineView({ path }: NodeProps) {
	const raw = useStringProp(path, "align", "start");
	const align: Align = ALIGNS.has(raw as Align) ? (raw as Align) : "start";
	// Nil or missing reads as the class default, wrapping on.
	const wrap = useProp<unknown>(path, "wrap", true) !== false;
	return (
		<LinePrimitive align={align} wrap={wrap}>
			<FlowProvider flow="inline">
				<NodeChildren path={path} cell={LineCell} indexed />
			</FlowProvider>
		</LinePrimitive>
	);
}

export const Line: NodeEntry = { component: LineView, fill: true };
