// Language by name, loaded on demand.
//
// `@codemirror/language-data` is a catalogue, not a bundle: each entry knows
// its names and aliases and holds a dynamic import for the grammar. So the kit
// ships the list of a hundred-odd languages for the cost of a table, and a
// grammar lands in its own chunk the first time a view asks for it. A name
// nothing matches renders unhighlighted rather than failing.

import type { LanguageDescription, LanguageSupport } from "@codemirror/language";
import { languages } from "@codemirror/language-data";

// LanguageDescription.matchLanguageName is fuzzy enough to find "python" in a
// longer string, which is not what a name means here. Exact name or alias.
function find(name: string): LanguageDescription | null {
	const key = name.trim().toLowerCase();
	if (!key) return null;
	for (const desc of languages) {
		if (desc.name.toLowerCase() === key || desc.alias.includes(key) || token(desc) === key) {
			return desc;
		}
	}
	return null;
}

/**
 * The one-word name a language is written with. A fence's info string ends at
 * the first space, so "MS SQL" cannot be a fence language: the lowercased name
 * when it is one word, else the first one-word alias, else the name hyphenated.
 */
function token(desc: LanguageDescription): string {
	const name = desc.name.toLowerCase();
	if (!/[\s`]/.test(name)) return name;
	const alias = desc.alias.find((a) => a !== "" && !/[\s`]/.test(a));
	return alias ?? name.replace(/[\s`]+/g, "-");
}

const cache = new Map<string, Promise<LanguageSupport | null>>();

/** The grammar for a language name, or null when the kit has none for it. */
export function loadLanguage(name: string): Promise<LanguageSupport | null> {
	const key = name.trim().toLowerCase();
	let hit = cache.get(key);
	if (!hit) {
		const desc = find(key);
		hit = desc ? desc.load().catch(() => null) : Promise.resolve(null);
		cache.set(key, hit);
	}
	return hit;
}

export type LanguageEntry = {
	/** What a fence or a `language` prop is written with: one word, no spaces or backticks. */
	value: string;
	/** The name as people spell it. */
	label: string;
	/** Other names that load the same grammar (`py`, `ts`). */
	aliases: readonly string[];
};

/** Every language the kit can highlight, for a picker. Names only, no grammar loaded. */
export const languageCatalogue: readonly LanguageEntry[] = languages
	.map((desc) => ({ value: token(desc), label: desc.name, aliases: desc.alias }))
	.sort((a, b) => a.label.localeCompare(b.label));

/** The catalogue entry a name or alias points at, or null for a name the kit has no grammar for. */
export function findLanguage(name: string): LanguageEntry | null {
	const desc = find(name);
	if (!desc) return null;
	const value = token(desc);
	return languageCatalogue.find((entry) => entry.value === value) ?? null;
}
