// The lens wire vocabulary.
//
// Two vocabularies, and keeping them apart is the whole idea:
//
//   KIND   the structural kind of a row - what kind of column it opens.
//          shape | mapping | sequence | leaf | unknown.
//   VTYPE  the type of the VALUE a row holds. str | int | float | bool |
//          bytes | none | empty | invalid | error | list | dict.
//
// A row shows the vtype glyph when it holds a value and the kind glyph when it
// does not (a shape slot, a key onto a shape). That is what makes a string, an
// int, a nested shape, an unset slot and a sentinel tell themselves apart at a
// glance without a legend.

import {
	Binary,
	Box,
	Braces,
	Brackets,
	CircleDashed,
	CircleSlash,
	Hash,
	type LucideIcon,
	ToggleLeft,
	TriangleAlert,
	Type,
} from "lucide-react";

/** One row in a column. Exactly what the server's cell builder ships. */
export type Entry = {
	key: string;
	kind: string;
	preview: string;
	navigable: boolean;
	/** Value type. "" when the row holds no value (a key onto a shape). */
	vtype?: string;
	/** Leaf rows only: the untruncated value for the reader pane. */
	text?: string;
	clipped?: boolean;
};

/** One column. `total` is what is there; `entries` is what fitted in the cap. */
export type Column = {
	kind: string;
	entries: Entry[];
	total: number;
};

const KIND_ICON: Record<string, LucideIcon> = {
	shape: Box,
	mapping: Braces,
	sequence: Brackets,
	leaf: Type,
	unknown: CircleSlash,
};

/** Human label for a column header. `mapping`/`sequence` are wire words. */
const KIND_LABEL: Record<string, string> = {
	shape: "shape",
	mapping: "dict",
	sequence: "list",
	leaf: "value",
	unknown: "unknown",
};

const VTYPE_ICON: Record<string, LucideIcon> = {
	str: Type,
	int: Hash,
	float: Hash,
	bool: ToggleLeft,
	bytes: Binary,
	none: CircleSlash,
	empty: CircleDashed,
	invalid: TriangleAlert,
	error: TriangleAlert,
	list: Brackets,
	dict: Braces,
};

/** Types that render as a word in a chip rather than as text. */
export const SENTINEL = new Set(["empty", "none", "invalid", "error"]);

/** The word a sentinel renders as, inside its chip. */
export const SENTINEL_LABEL: Record<string, string> = {
	empty: "empty",
	none: "none",
	invalid: "invalid",
	error: "error",
};

export function kindLabel(kind: string): string {
	return KIND_LABEL[kind] ?? kind;
}

export function kindIcon(kind: string): LucideIcon {
	return KIND_ICON[kind] ?? KIND_ICON.unknown;
}

/**
 * The glyph for one row. The value type wins when the row holds a value; the
 * structural kind carries it otherwise (a shape slot has not been read, a key
 * onto a shape is a way in and not a value).
 */
export function rowIcon(kind: string, vtype: string): LucideIcon {
	return VTYPE_ICON[vtype] ?? KIND_ICON[kind] ?? KIND_ICON.unknown;
}

/**
 * Glyph colour. Two channels, deliberately: the GLYPH says what type it is and
 * the COLOUR says only whether the row goes anywhere. Five kinds in five hues
 * turns a 200-row column into confetti and leans on colour for a distinction
 * the glyph already makes. So navigable rows take the blue secondary, terminal
 * rows stay muted, and only a genuinely bad state earns a status hue.
 */
export function glyphTone(vtype: string, navigable: boolean): string {
	if (vtype === "invalid" || vtype === "error") return "text-status-danger";
	if (vtype === "empty" || vtype === "none") return "text-text-muted";
	return navigable ? "text-accent-2" : "text-text-muted";
}

/** The trailing value cell's type tier. */
export function valueTone(vtype: string): string {
	switch (vtype) {
		case "int":
		case "float":
			return "text-accent-2 tabular-nums";
		case "bool":
			return "text-accent";
		case "str":
			return "text-text-secondary";
		case "invalid":
		case "error":
			return "text-status-danger";
		case "none":
		case "empty":
			return "text-text-muted";
		default:
			return "text-text-secondary";
	}
}
