// Counts as the kit's data components print them: full digits up to 9,999,
// compact past it (12.4K), so a column of counts keeps one width. The full
// number goes in a title or label when the compact one is shown.

const fullFormat = new Intl.NumberFormat("en");
const compactFormat = new Intl.NumberFormat("en", {
	notation: "compact",
	maximumFractionDigits: 1,
});

/** Full digits up to 9,999, compact past it (12.4K). */
export function formatCount(n: number): string {
	return n >= 10_000 ? compactFormat.format(n) : fullFormat.format(n);
}

/** Every digit, grouped (1,204,311). */
export function formatFullCount(n: number): string {
	return fullFormat.format(n);
}
