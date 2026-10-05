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
		if (desc.name.toLowerCase() === key || desc.alias.includes(key)) return desc;
	}
	return null;
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
