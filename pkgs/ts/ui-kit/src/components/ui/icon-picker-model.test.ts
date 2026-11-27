// The icon picker model: the stored spelling, the emoji shape, recent picks
// and the search.

import { afterEach, describe, expect, it } from "vitest";
import {
	emojiSections,
	formatIcon,
	iconKind,
	normalizeIcon,
	packSections,
	parseIcon,
	pushRecent,
	RECENT_MAX,
	readRecent,
	sectionsFor,
	shapeEmoji,
} from "./icon-picker-model";

describe("the stored spelling", () => {
	it("reads a lucide name with or without the prefix, in any case", () => {
		expect(parseIcon("lucide:folder")).toEqual({ kind: "lucide", name: "folder" });
		expect(parseIcon("folder")).toEqual({ kind: "lucide", name: "folder" });
		expect(parseIcon(" FileText ")).toEqual({ kind: "lucide", name: "file-text" });
		expect(parseIcon("Gamepad2")).toEqual({ kind: "lucide", name: "gamepad-2" });
	});

	it("reads an emoji", () => {
		expect(parseIcon("emoji:🌱")).toEqual({ kind: "emoji", char: "🌱" });
	});

	it("reads junk as none", () => {
		for (const raw of ["", "  ", "emoji:", "lucide:no-such-icon", "mdi:home", 7, null, undefined]) {
			expect(parseIcon(raw)).toBeNull();
		}
	});

	it("writes one spelling back", () => {
		expect(formatIcon({ kind: "lucide", name: "folder" })).toBe("lucide:folder");
		expect(formatIcon({ kind: "emoji", char: "🐱" })).toBe("emoji:🐱");
		expect(formatIcon(null)).toBe("");
		expect(normalizeIcon("FileText")).toBe("lucide:file-text");
		expect(normalizeIcon("nope:x")).toBe("");
		expect(iconKind("emoji:🐱")).toBe("emoji");
		expect(iconKind("")).toBeNull();
	});
});

describe("emoji", () => {
	it("sentence cases the groups and drops emoji past 15.0", () => {
		const groups = shapeEmoji([
			{
				name: "Smileys & Emotion",
				emojis: [
					{ emoji: "😀", name: "grinning face", emoji_version: "1.0" },
					{ emoji: "🫨", name: "shaking face", emoji_version: "15.0" },
					{ emoji: "🙂‍↔️", name: "head shaking horizontally", emoji_version: "15.1" },
				],
			},
			{ name: "Empty", emojis: [{ emoji: "x", name: "new", emoji_version: "16.0" }] },
		]);
		expect(groups).toEqual([
			{
				label: "Smileys & emotion",
				emojis: [
					{ char: "😀", name: "grinning face" },
					{ char: "🫨", name: "shaking face" },
				],
			},
		]);
	});
});

describe("recent picks", () => {
	afterEach(() => window.localStorage.clear());

	it("keeps picks newest first under the caller's key, once each", () => {
		pushRecent("a.icons", "lucide:folder");
		pushRecent("a.icons", "emoji:🐱");
		pushRecent("a.icons", "lucide:folder");
		expect(readRecent("a.icons")).toEqual(["lucide:folder", "emoji:🐱"]);
		expect(readRecent("b.icons")).toEqual([]);
	});

	it("caps the list and reads junk as nothing picked", () => {
		for (let i = 0; i < RECENT_MAX + 5; i++) pushRecent("k", `emoji:${i}`);
		expect(readRecent("k")).toHaveLength(RECENT_MAX);
		window.localStorage.setItem("k", "{not json");
		expect(readRecent("k")).toEqual([]);
		window.localStorage.setItem("k", JSON.stringify(["lucide:folder", 3, "nope:x"]));
		expect(readRecent("k")).toEqual(["lucide:folder"]);
	});
});

describe("the grid's sections", () => {
	const icons = packSections([
		{ label: "Work", icons: [["timer", "stopwatch"], ["calendar"], ["no-such-icon"]] },
		{ label: "Dev", icons: [["cpu", "chip"]] },
	]);
	const emoji = emojiSections([{ label: "Animals", emojis: [{ char: "🐱", name: "cat face" }] }]);

	it("turns a pack into cells, leaving out names lucide does not have", () => {
		expect(icons[0].cells.map((c) => c.value)).toEqual(["lucide:timer", "lucide:calendar"]);
		expect(emoji[0].cells[0]).toMatchObject({ value: "emoji:🐱", label: "cat face" });
	});

	it("filters on every word, over name, keywords and group", () => {
		const hit = (q: string) =>
			sectionsFor(icons, [], q).flatMap((s) => s.cells.map((c) => c.value));
		expect(hit("stopwatch")).toEqual(["lucide:timer"]);
		expect(hit("dev chip")).toEqual(["lucide:cpu"]);
		expect(hit("work nothing")).toEqual([]);
	});

	it("leads with the recent picks it knows, only while there is no search", () => {
		const shown = sectionsFor(icons, ["lucide:cpu", "lucide:gone"], "");
		expect(shown[0]).toMatchObject({ label: "Recent" });
		expect(shown[0].cells.map((c) => c.value)).toEqual(["lucide:cpu"]);
		expect(sectionsFor(icons, ["lucide:cpu"], "timer")[0].label).toBe("Work");
	});
});
