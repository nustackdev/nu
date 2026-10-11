// Line -- children inline, wrapping like a paragraph. Draws its children in
// the kit Line primitive, each one followed by a word space (`LineRun` as
// the child cell), and hands them an "inline" flow.
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

import { Line as LinePrimitive, LineRun } from "../../components/ui/line";
import {
	FlowProvider,
	NodeChildren,
	type NodeEntry,
	type NodeProps,
	useProp,
	useStringProp,
} from "../../tree";

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
				<NodeChildren path={path} cell={LineRun} />
			</FlowProvider>
		</LinePrimitive>
	);
}

export const Line: NodeEntry = { component: LineView, fill: true };
