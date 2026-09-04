// Shared Shiki highlighter for the Code primitive.
//
// One highlighter instance, reused across renders. Languages and themes load
// on demand; `codeToHtml` returns spans with `--shiki-light` / `--shiki-dark`
// CSS vars so the `.dark` class flip drives the palette (see index.css).

import { useEffect, useState } from "react";
import {
	type BundledLanguage,
	type BundledTheme,
	bundledLanguages,
	bundledThemes,
	createHighlighter,
	type HighlighterGeneric,
} from "shiki";

const LIGHT_THEME: BundledTheme = "github-light";
const DARK_THEME: BundledTheme = "github-dark";

type Highlighter = HighlighterGeneric<BundledLanguage, BundledTheme>;

let highlighterPromise: Promise<Highlighter> | null = null;
const loadedLangs = new Set<string>();

function getHighlighter(): Promise<Highlighter> {
	if (!highlighterPromise) {
		highlighterPromise = createHighlighter({
			themes: [LIGHT_THEME, DARK_THEME],
			langs: [],
		});
	}
	return highlighterPromise;
}

function normalizeLang(lang: string): BundledLanguage | null {
	const key = lang.toLowerCase();
	if (key in bundledLanguages) return key as BundledLanguage;
	return null;
}

async function loadLang(h: Highlighter, lang: BundledLanguage): Promise<void> {
	if (loadedLangs.has(lang)) return;
	await h.loadLanguage(lang);
	loadedLangs.add(lang);
}

export function useShikiHtml(code: string, language: string | undefined): string | null {
	const [html, setHtml] = useState<string | null>(null);

	useEffect(() => {
		if (!language) {
			setHtml(null);
			return;
		}
		const lang = normalizeLang(language);
		if (!lang) {
			setHtml(null);
			return;
		}

		let cancelled = false;
		(async () => {
			const h = await getHighlighter();
			await loadLang(h, lang);
			if (cancelled) return;
			const out = h.codeToHtml(code, {
				lang,
				themes: { light: LIGHT_THEME, dark: DARK_THEME },
				defaultColor: false,
			});
			setHtml(out);
		})().catch(() => {
			if (!cancelled) setHtml(null);
		});

		return () => {
			cancelled = true;
		};
	}, [code, language]);

	return html;
}

// Exported for docs/tests that want to warm the highlighter up front.
export { bundledThemes, LIGHT_THEME, DARK_THEME };
