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

const BYTE_UNITS = ["B", "KB", "MB", "GB", "TB"];
const byteFormats = [0, 1].map(
	(digits) => new Intl.NumberFormat("en", { maximumFractionDigits: digits }),
);

/**
 * A byte count for people, in decimal units the way a file manager shows
 * them: 812 B, 4.2 KB, 1.3 GB. One decimal under 100, none from 100 up, and a
 * value that would round to 1,000 moves up a unit (999,999 is 1 MB).
 */
export function formatBytes(n: number): string {
	let value = Number.isFinite(n) && n > 0 ? n : 0;
	let unit = 0;
	while (unit < BYTE_UNITS.length - 1) {
		const digits = unit === 0 || value >= 100 ? 0 : 1;
		if (Number(value.toFixed(digits)) < 1000) break;
		value /= 1000;
		unit += 1;
	}
	const digits = unit === 0 || value >= 100 ? 0 : 1;
	return `${byteFormats[digits].format(value)} ${BYTE_UNITS[unit]}`;
}
