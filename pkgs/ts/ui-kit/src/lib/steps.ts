// The space scale as classes: `gap` and `padding` on every container are an
// int step from 0 to 16, a step being 4px (`--spacing`).
//
// Tailwind finds classes by scanning source text, so a class templated from
// a number at run time would never be generated. Every step is written out
// here instead. A value off the scale reads as unset (`stepClass` returns
// undefined), so the container keeps its own look.

export const SPACE_STEPS = 16;

export const GAP_CLASSES: Record<number, string> = {
	0: "gap-0",
	1: "gap-1",
	2: "gap-2",
	3: "gap-3",
	4: "gap-4",
	5: "gap-5",
	6: "gap-6",
	7: "gap-7",
	8: "gap-8",
	9: "gap-9",
	10: "gap-10",
	11: "gap-11",
	12: "gap-12",
	13: "gap-13",
	14: "gap-14",
	15: "gap-15",
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
	7: "p-7",
	8: "p-8",
	9: "p-9",
	10: "p-10",
	11: "p-11",
	12: "p-12",
	13: "p-13",
	14: "p-14",
	15: "p-15",
	16: "p-16",
};

/** A step off the wire: a whole number from 0 to 16, or undefined for anything else. */
export function readStep(raw: unknown): number | undefined {
	return typeof raw === "number" && Number.isInteger(raw) && raw >= 0 && raw <= SPACE_STEPS
		? raw
		: undefined;
}

/** The class for step `n` on `ladder`, or undefined when `n` is not a step. */
export function stepClass(ladder: Record<number, string>, n: unknown): string | undefined {
	const step = readStep(n);
	return step === undefined ? undefined : ladder[step];
}
