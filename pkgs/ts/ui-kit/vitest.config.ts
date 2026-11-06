/// <reference types="@vitest/browser/providers/playwright" />
import react from "@vitejs/plugin-react";
import { configDefaults, defineConfig } from "vitest/config";

// Two shapes of test live here, and they need different hosts.
//
// Logic tests (`*.test.{ts,tsx}`) run in jsdom: the markdown round trip is pure
// data, and the editor test mounts a real ProseMirror view to check what a
// transaction does to the document. jsdom has a DOM but lays nothing out, so a
// caret position, a wrapped line or a coordinate means nothing there.
//
// Contract tests (`*.browser.test.{ts,tsx}`) run in a real Firefox, headless,
// driven by Playwright. They are for what only layout can answer: where a
// line wraps, whether the caret sits on the first or last visual line, what a
// real keypress does at an edge. Keys arrive through vitest's `userEvent`, so
// the browser itself turns them into input, not a dispatch we wrote.
//
// `vitest run` runs both. The browser project needs a Playwright Firefox build
// matching the `playwright` devDependency in ~/.cache/ms-playwright.
//
// The kit has no build config of its own (it ships source), so this is the
// only vite-shaped file in the package.
const browserTests = "src/**/*.browser.test.{ts,tsx}";

export default defineConfig({
	plugins: [react()],
	test: {
		projects: [
			{
				extends: true,
				test: {
					name: "jsdom",
					environment: "jsdom",
					include: ["src/**/*.test.{ts,tsx}"],
					exclude: [...configDefaults.exclude, browserTests],
				},
			},
			{
				extends: true,
				test: {
					name: "browser",
					include: [browserTests],
					browser: {
						enabled: true,
						provider: "playwright",
						headless: true,
						instances: [{ browser: "firefox" }],
						// One file at a time. Headless, vitest runs browser files in
						// parallel iframes of one page, and a page has one focus and
						// one keyboard: a real click in one file's editor takes the
						// key another file is pressing at that moment.
						fileParallelism: false,
					},
				},
			},
		],
	},
});
