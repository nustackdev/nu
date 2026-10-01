// Shortcut key names, and what each platform calls them.
//
// A shortcut is written once, by name (`["mod", "K"]`), and drawn the way the
// reader's platform spells it: glyphs run together on a Mac (`⌘K`), words
// joined by `+` elsewhere (`Ctrl+K`). `mod` is the one that moves: command on
// a Mac, control everywhere else, the same key a handler reads as
// `metaKey || ctrlKey`.
//
// A name not in the table is a key as typed: a letter is shown upper case, and
// anything longer passes through untouched.

export type Platform = "mac" | "other";

type Key = { mac: string; other: string; spoken: string; spokenMac?: string };

const KEYS: Record<string, Key> = {
	mod: { mac: "⌘", other: "Ctrl", spoken: "Control", spokenMac: "Command" },
	cmd: { mac: "⌘", other: "Meta", spoken: "Meta", spokenMac: "Command" },
	ctrl: { mac: "⌃", other: "Ctrl", spoken: "Control" },
	alt: { mac: "⌥", other: "Alt", spoken: "Alt", spokenMac: "Option" },
	shift: { mac: "⇧", other: "Shift", spoken: "Shift" },
	enter: { mac: "↵", other: "↵", spoken: "Enter" },
	esc: { mac: "Esc", other: "Esc", spoken: "Escape" },
	tab: { mac: "⇥", other: "Tab", spoken: "Tab" },
	backspace: { mac: "⌫", other: "Backspace", spoken: "Backspace" },
	delete: { mac: "⌦", other: "Del", spoken: "Delete" },
	space: { mac: "Space", other: "Space", spoken: "Space" },
	up: { mac: "↑", other: "↑", spoken: "Up arrow" },
	down: { mac: "↓", other: "↓", spoken: "Down arrow" },
	left: { mac: "←", other: "←", spoken: "Left arrow" },
	right: { mac: "→", other: "→", spoken: "Right arrow" },
};

KEYS.meta = KEYS.cmd;
KEYS.option = KEYS.alt;
KEYS.return = KEYS.enter;
KEYS.escape = KEYS.esc;
KEYS.del = KEYS.delete;

let mac: boolean | undefined;

/** Whether the reader is on a Mac (or an iPhone or iPad). False with no browser. */
export function isMac(): boolean {
	if (mac === undefined) {
		mac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.userAgent);
	}
	return mac;
}

function platformOf(platform?: Platform): Platform {
	return platform ?? (isMac() ? "mac" : "other");
}

/** One key as its platform draws it. */
export function keyLabel(name: string, platform?: Platform): string {
	const key = KEYS[name.toLowerCase()];
	if (key) return key[platformOf(platform)];
	return name.length === 1 ? name.toUpperCase() : name;
}

/** One key as a screen reader should say it. */
export function keySpoken(name: string, platform?: Platform): string {
	const key = KEYS[name.toLowerCase()];
	if (!key) return name.length === 1 ? name.toUpperCase() : name;
	return platformOf(platform) === "mac" ? (key.spokenMac ?? key.spoken) : key.spoken;
}

/** A whole shortcut as text, for a title or an `aria-keyshortcuts`-style hint. */
export function formatShortcut(keys: readonly string[], platform?: Platform): string {
	const p = platformOf(platform);
	return keys.map((k) => keyLabel(k, p)).join(p === "mac" ? "" : "+");
}
