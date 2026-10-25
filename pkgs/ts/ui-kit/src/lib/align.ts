// Text alignment off the wire: start, center or end, with left and right
// read as the older spelling of start and end. Text, Heading and Divider all
// take `align` this way; anything else falls back.

export type Align = "start" | "center" | "end";

const ALIGNS: Record<string, Align> = {
	start: "start",
	left: "start",
	center: "center",
	end: "end",
	right: "end",
};

/** An `align` prop as start / center / end, or `fallback` for anything unknown. */
export function normAlign(v: unknown, fallback: Align = "start"): Align {
	return (typeof v === "string" && ALIGNS[v]) || fallback;
}

/** The text-align class per alignment, logical so it follows the writing direction. */
export const TEXT_ALIGN: Record<Align, string> = {
	start: "text-start",
	center: "text-center",
	end: "text-end",
};
