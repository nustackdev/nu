// Icon picker model: the stored spelling of an icon, the emoji set, the
// recent picks and the search. No React.
//
// An icon is stored as one string:
//
//   "lucide:<name>"   any lucide glyph, by lucide's own kebab name
//   "emoji:<char>"    an emoji, drawn as text
//   "" or absent      no icon
//
// A bare name, no prefix, is a lucide one, the way a node names its icon on
// the wire. A name lucide does not have, or any other prefix, reads as no
// icon, so the caller falls back to whatever it shows by default.
//
// The emoji are `unicode-emoji-json`'s by-group file: every fully qualified
// emoji with its Unicode name and group, bundled, never fetched from anywhere
// else. It is a dynamic import, so a bundler puts it in a chunk of its own and
// a page does not carry it until someone opens the picker. Emoji newer than
// 15.0 are left out (a system font that cannot draw one shows a box, and 15.0
// is what the platforms people run draw today), and skin tone variants are not
// offered, only the default.
//
// Recent picks are per browser, in localStorage under a key the caller names,
// and a convenience only: storage that is blocked, full or holding junk reads
// as nothing picked yet.

import { isIconName } from "../../lib/icons";
import { readStored, writeStored } from "../../lib/resize";
import type { IconPackGroup } from "./icon-pack";

/* ============================== The value =============================== */

export const LUCIDE_PREFIX = "lucide:";
export const EMOJI_PREFIX = "emoji:";

/** An icon, read: a lucide glyph by name or an emoji by its character. */
export type IconValue = { kind: "lucide"; name: string } | { kind: "emoji"; char: string };

/** `FileText`, `fileText` and `file-text` are one name; so are `Gamepad2` and `gamepad-2`. */
function kebab(name: string): string {
	return name
		.trim()
		.replace(/([a-z0-9])([A-Z])/g, "$1-$2")
		.replace(/([a-zA-Z])(\d)/g, "$1-$2")
		.toLowerCase();
}

/** The icon a stored value names, or null for none (empty, unknown, not a string). */
export function parseIcon(raw: unknown): IconValue | null {
	if (typeof raw !== "string") return null;
	const value = raw.trim();
	if (!value) return null;
	if (value.startsWith(EMOJI_PREFIX)) {
		const char = value.slice(EMOJI_PREFIX.length).trim();
		return char ? { kind: "emoji", char } : null;
	}
	let name = value;
	if (value.startsWith(LUCIDE_PREFIX)) name = value.slice(LUCIDE_PREFIX.length);
	else if (value.includes(":")) return null;
	name = kebab(name);
	return isIconName(name) ? { kind: "lucide", name } : null;
}

/** The stored spelling of an icon, "" for none. */
export function formatIcon(icon: IconValue | null): string {
	if (!icon) return "";
	return icon.kind === "emoji" ? `${EMOJI_PREFIX}${icon.char}` : `${LUCIDE_PREFIX}${icon.name}`;
}

/** A stored value in its one spelling: "FileText" reads "lucide:file-text", junk reads "". */
export function normalizeIcon(raw: unknown): string {
	return formatIcon(parseIcon(raw));
}

/* ============================== Emoji ==================================== */

export type Emoji = {
	char: string;
	/** Unicode's name, eg "grinning face". */
	name: string;
};

export type EmojiGroup = { label: string; emojis: Emoji[] };

type RawEmoji = {
	name: string;
	emojis: { emoji: string; name: string; emoji_version: string }[];
}[];

/** The newest emoji version offered. */
const NEWEST_EMOJI = 15.0;

/** "Smileys & Emotion" reads "Smileys & emotion": UI copy is sentence case. */
function sentence(label: string): string {
	const lower = label.toLowerCase();
	return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** The by-group file, shaped for the picker. Pure, so it is testable without the data. */
export function shapeEmoji(raw: RawEmoji): EmojiGroup[] {
	return raw
		.map((group) => ({
			label: sentence(group.name),
			emojis: group.emojis
				.filter((e) => Number.parseFloat(e.emoji_version) <= NEWEST_EMOJI)
				.map((e) => ({ char: e.emoji, name: e.name })),
		}))
		.filter((group) => group.emojis.length > 0);
}

let loading: Promise<EmojiGroup[]> | null = null;

/** The emoji, once. A failed load is forgotten, so the next open tries again. */
export function loadEmoji(): Promise<EmojiGroup[]> {
	loading ??= import("unicode-emoji-json/data-by-group.json").then(
		(mod) => shapeEmoji(mod.default as RawEmoji),
		(err: unknown) => {
			loading = null;
			throw err;
		},
	);
	return loading;
}

/* ============================== Recent picks ============================ */

/** Where the kit keeps recent picks when the caller names no key of its own. */
export const RECENT_ICONS_KEY = "nu.icons.recent";

/** How many recent picks are kept. Two rows of the desktop grid. */
export const RECENT_MAX = 18;

/** The picks kept under `key`, newest first. */
export function readRecent(key: string): string[] {
	try {
		const raw = readStored(key);
		const list: unknown = raw ? JSON.parse(raw) : [];
		if (!Array.isArray(list)) return [];
		return list
			.filter((v): v is string => typeof v === "string" && parseIcon(v) !== null)
			.slice(0, RECENT_MAX);
	} catch {
		return [];
	}
}

/** Put `icon` first under `key`. Storage that throws keeps nothing, quietly. */
export function pushRecent(key: string, icon: string): void {
	const next = [icon, ...readRecent(key).filter((v) => v !== icon)].slice(0, RECENT_MAX);
	writeStored(key, JSON.stringify(next));
}

/* ============================== The grid ================================= */

/** The picker's two kinds, one tab each. */
export type IconKind = "emoji" | "lucide";

export type IconCell = {
	/** The stored spelling a pick hands back. */
	value: string;
	/** What it is called, for a screen reader and the tooltip. */
	label: string;
	icon: IconValue;
	/** Everything the search matches on, lower case. */
	haystack: string;
};

export type IconSection = { label: string; cells: IconCell[] };

/** A pack as the grid's sections. Names lucide does not have are left out. */
export function packSections(pack: readonly IconPackGroup[]): IconSection[] {
	return pack.map(({ label, icons }) => ({
		label,
		cells: icons.flatMap(([raw, keywords = ""]) => {
			const icon = parseIcon(raw);
			if (icon?.kind !== "lucide") return [];
			const words = icon.name.replace(/-/g, " ");
			return [
				{
					value: formatIcon(icon),
					label: words,
					icon,
					haystack: `${words} ${icon.name} ${keywords} ${label}`.toLowerCase(),
				},
			];
		}),
	}));
}

/** The emoji as the grid's sections. */
export function emojiSections(groups: EmojiGroup[]): IconSection[] {
	return groups.map((group) => ({
		label: group.label,
		cells: group.emojis.map((e) => ({
			value: formatIcon({ kind: "emoji", char: e.char }),
			label: e.name,
			icon: { kind: "emoji", char: e.char } as const,
			haystack: `${e.name} ${group.label}`.toLowerCase(),
		})),
	}));
}

/**
 * The sections a tab shows for a query. A query keeps the cells with every
 * word of it somewhere in their words; no query puts the recent picks found
 * among `all` first, as their own section.
 */
export function sectionsFor(all: IconSection[], recent: string[], query: string): IconSection[] {
	const words = query.toLowerCase().split(/\s+/).filter(Boolean);
	if (words.length > 0) {
		return all
			.map((s) => ({
				label: s.label,
				cells: s.cells.filter((c) => words.every((w) => c.haystack.includes(w))),
			}))
			.filter((s) => s.cells.length > 0);
	}
	const byValue = new Map(all.flatMap((s) => s.cells.map((c) => [c.value, c] as const)));
	const mine = recent.flatMap((v) => byValue.get(v) ?? []);
	return mine.length > 0 ? [{ label: "Recent", cells: mine }, ...all] : all;
}

/** The kind of a stored value, null for none. */
export function iconKind(value: string): IconKind | null {
	return parseIcon(value)?.kind ?? null;
}
