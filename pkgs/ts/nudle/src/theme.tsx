// Theme for the nudle page: dark or light, flipped by one `.dark` class on
// <html>, which is what the kit's tokens read.
//
// With no stored choice the page follows the system theme and keeps in step
// with it. Once the user flips the toggle, that choice wins and is kept in
// localStorage. index.html applies the same rule before first paint, so there
// is no flash; this module owns every change after that.

import { useSyncExternalStore } from "react";
import { IconButton } from "@nustackdev/ui-kit";

type Theme = "dark" | "light";

const KEY = "nudle.theme";
const system = window.matchMedia("(prefers-color-scheme: dark)");
const subscribers = new Set<() => void>();

function stored(): Theme | null {
	try {
		const v = window.localStorage.getItem(KEY);
		return v === "dark" || v === "light" ? v : null;
	} catch {
		return null;
	}
}

let current: Theme = stored() ?? (system.matches ? "dark" : "light");

function paint(theme: Theme): void {
	document.documentElement.classList.toggle("dark", theme === "dark");
	document.documentElement.style.colorScheme = theme;
}

function set(theme: Theme, persist: boolean): void {
	current = theme;
	paint(theme);
	if (persist) {
		try {
			window.localStorage.setItem(KEY, theme);
		} catch {
			// Not persisted; the session still honours it.
		}
	}
	for (const cb of subscribers) cb();
}

paint(current);
system.addEventListener("change", () => {
	if (stored() === null) set(system.matches ? "dark" : "light", false);
});

function subscribe(cb: () => void): () => void {
	subscribers.add(cb);
	return () => subscribers.delete(cb);
}

const getTheme = () => current;

function Sun() {
	return (
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<circle cx="12" cy="12" r="4" />
			<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
		</svg>
	);
}

function Moon() {
	return (
		<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
			<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
		</svg>
	);
}

/** Flips dark and light. Shows the theme it switches to. */
export function ThemeToggle() {
	const theme = useSyncExternalStore(subscribe, getTheme, getTheme);
	const next: Theme = theme === "dark" ? "light" : "dark";
	return (
		<IconButton variant="ghost" size="sm" aria-label={`Switch to ${next} theme`} title={`${next === "dark" ? "Dark" : "Light"} theme`} onClick={() => set(next, true)}>
			{theme === "dark" ? <Sun /> : <Moon />}
		</IconButton>
	);
}
