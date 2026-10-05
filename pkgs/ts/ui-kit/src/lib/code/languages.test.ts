// The language catalogue, as a fence writes it.
//
// A fence's info string ends at the first space and cannot hold a backtick,
// so every name the picker offers has to be one such word, and that word has
// to load the same grammar the full name does.

import { describe, expect, it } from "vitest";
import { findLanguage, languageCatalogue, loadLanguage } from "./languages";

describe("language catalogue", () => {
	it("offers only names a fence line can carry", () => {
		expect(languageCatalogue.filter((entry) => /[\s`]/.test(entry.value))).toEqual([]);
	});

	it("resolves every offered name back to its own entry", () => {
		for (const entry of languageCatalogue) expect(findLanguage(entry.value)).toBe(entry);
	});

	it("loads a grammar for a name that had to be rewritten", async () => {
		const sql = findLanguage("MS SQL");
		expect(sql?.value).toBe("ms-sql");
		expect(await loadLanguage("ms-sql")).not.toBeNull();
	});
});
