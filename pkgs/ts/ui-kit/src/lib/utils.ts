import { type ClassValue, clsx } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// The kit's type scale has a `display` step past 3xl. Unregistered, the merge
// reads `text-display` as a color, so a tone class (`text-text-muted`) after
// it would drop the size.
const twMerge = extendTailwindMerge({ extend: { theme: { text: ["display"] } } });

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// Where a control's focus ring sits, as the `ring` variant on every control
// that takes focus. `offset` floats it 2px clear of the box (a11y.md §1);
// `inset` draws it inside, for dense rows where a parent's overflow would
// clip the offset.
export const ringVariants = {
	offset: "focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
	inset: "focus-visible:ring-inset",
};
