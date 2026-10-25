// The spacing ladder as classes, for a container whose `gap` or `padding`
// comes off the wire as a number (Row, Column, Form, PageSection).
//
// Tailwind finds classes by scanning source text, so a class templated from
// a number at run time would never be generated. Every step is written out
// here instead, and a value off the ladder snaps to the nearest step rather
// than to a fixed fallback.

export const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	8: "gap-8",
	10: "gap-10",
	12: "gap-12",
	16: "gap-16",
};

export const PADDING_CLASSES: Record<number, string> = {
	0: "p-0",
	1: "p-1",
	2: "p-2",
	3: "p-3",
	4: "p-4",
	5: "p-5",
	6: "p-6",
	8: "p-8",
	10: "p-10",
	12: "p-12",
	16: "p-16",
};

/** The class for the ladder step nearest `n` (ties go to the smaller step). */
export function stepClass(ladder: Record<number, string>, n: number): string {
	let best = 0;
	for (const key of Object.keys(ladder).map(Number)) {
		if (Math.abs(key - n) < Math.abs(best - n)) best = key;
	}
	return ladder[best];
}
