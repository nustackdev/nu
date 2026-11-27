// Touch shots: Storybook stories screenshotted the way a phone sees them.
//
//   npm run shots -- --grep popover            stories whose id matches
//   npm run shots -- --grep "select|combobox" --webkit
//   npm run shots -- --grep popover --url http://localhost:6006
//
// For each story, three shots:
//
//   phone   375x812, touch emulated (coarse pointer, no hover). The kit reads
//           touch mode from the device here, the same path a real phone takes
//   tablet  768x1024, touch emulated
//   narrow  a desktop page, mouse, the story in a 360px column (the Frame
//           toolbar). Layout follows its own width: it should match the
//           phone's layout with desktop interactions
//
// Chromium always; `--webkit` adds WebKit for the two touch shots, a rough
// Safari check. Real iOS keyboard and safe areas still need a real phone.
//
// Without `--url` it boots its own Storybook on a free port and stops it when
// done, so parallel runs (one per worktree) do not collide. Shots land in
// `.shots/` (`--out` to move them) with an index.html contact sheet.
// A story that opens an overlay should open at load (`defaultOpen`) or in a
// `play` function; the shot waits for the page to settle.
//
// A shot fails on the wrong touch mode, a page error, Storybook's own error
// page (its error display, `body.sb-show-errordisplay`, or no preview), or a
// story that drew nothing (an empty root and nothing portalled to the body).
// The error page is mostly vite's first load: it optimises a dependency,
// reloads, and the story's module fetch fails meanwhile ("Failed to fetch
// dynamically imported module"). So a broken load is retried once, after a
// short wait, before it counts.

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { chromium, webkit } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");

const { values: args } = parseArgs({
	options: {
		grep: { type: "string" },
		url: { type: "string" },
		out: { type: "string", default: path.join(root, ".shots") },
		webkit: { type: "boolean", default: false },
		settle: { type: "string", default: "700" },
	},
});
if (!args.grep) {
	console.error("usage: npm run shots -- --grep <story id regex> [--webkit] [--url <storybook>] [--out <dir>]");
	process.exit(2);
}

const MODES = [
	{ name: "phone", touch: true, viewport: { width: 375, height: 812 } },
	{ name: "tablet", touch: true, viewport: { width: 768, height: 1024 } },
	{ name: "narrow", touch: false, viewport: { width: 1280, height: 800 }, globals: "frame:narrow" },
];

function freePort() {
	return new Promise((resolve, reject) => {
		const srv = createServer();
		srv.listen(0, () => {
			const { port } = srv.address();
			srv.close(() => resolve(port));
		});
		srv.on("error", reject);
	});
}

async function waitFor(url, ms) {
	const end = Date.now() + ms;
	while (Date.now() < end) {
		try {
			const r = await fetch(url);
			if (r.ok) return;
		} catch {}
		await new Promise((r) => setTimeout(r, 500));
	}
	throw new Error(`storybook did not come up at ${url}`);
}

// What the loaded story page shows: Storybook's error page (its message), an
// empty story, or neither. Read in the page.
function readStory() {
	const body = document.body;
	const shown = (cls) => body.classList.contains(cls);
	if (shown("sb-show-errordisplay") || shown("sb-show-nopreview")) {
		const message = document.querySelector("#error-message")?.textContent?.trim();
		return { error: message || (shown("sb-show-nopreview") ? "no preview" : "storybook error page") };
	}
	const text = body.innerText || "";
	const m = text.match(/Failed to fetch dynamically imported module[^\n]*/);
	if (m) return { error: m[0] };
	const root = document.querySelector("#storybook-root");
	const docs = document.querySelector("#storybook-docs");
	const drawn = (el) => !!el && (el.children.length > 0 || (el.textContent || "").trim() !== "");
	// Storybook's own body children; anything else is a story's portal.
	const own = (el) =>
		el.id === "storybook-root" ||
		el.id === "storybook-docs" ||
		el.classList.contains("sb-wrapper") ||
		["SCRIPT", "STYLE", "LINK", "TEMPLATE", "NOSCRIPT"].includes(el.tagName);
	const portalled = [...body.children].some((el) => !own(el) && drawn(el));
	if (!drawn(root) && !drawn(docs) && !portalled) return { error: "story root is empty" };
	return { error: null };
}

async function bootStorybook() {
	const port = await freePort();
	const proc = spawn("npx", ["storybook", "dev", "--ci", "--no-open", "--quiet", "-p", String(port)], {
		cwd: root,
		stdio: ["ignore", "ignore", "inherit"],
		detached: true,
	});
	const url = `http://localhost:${port}`;
	await waitFor(`${url}/index.json`, 180_000);
	return { url, stop: () => process.kill(-proc.pid, "SIGTERM") };
}

const sb = args.url ? { url: args.url.replace(/\/$/, ""), stop: () => {} } : await bootStorybook();
let failed = 0;
try {
	const index = await (await fetch(`${sb.url}/index.json`)).json();
	const re = new RegExp(args.grep, "i");
	const stories = Object.values(index.entries).filter((e) => e.type === "story" && re.test(e.id));
	if (!stories.length) throw new Error(`no story id matches /${args.grep}/i`);
	console.log(`${stories.length} stories`);

	mkdirSync(args.out, { recursive: true });
	const engines = [["chromium", chromium], ...(args.webkit ? [["webkit", webkit]] : [])];
	const rows = [];
	for (const [engine, type] of engines) {
		const browser = await type.launch();
		for (const mode of MODES) {
			if (engine === "webkit" && !mode.touch) continue;
			const ctx = await browser.newContext({
				viewport: mode.viewport,
				deviceScaleFactor: 2,
				hasTouch: mode.touch,
				isMobile: mode.touch && engine === "chromium" ? true : undefined,
			});
			const page = await ctx.newPage();
			for (const story of stories) {
				let errors = [];
				page.removeAllListeners("pageerror");
				page.on("pageerror", (e) => errors.push(e.message));
				const q = `id=${story.id}&viewMode=story${mode.globals ? `&globals=${mode.globals}` : ""}`;
				const load = async () => {
					errors = [];
					await page.goto(`${sb.url}/iframe.html?${q}`, { waitUntil: "networkidle" });
					// The story drawn, or Storybook's error page up, whichever first.
					await page
						.waitForFunction(
							() =>
								document.querySelector("#storybook-root > *, #storybook-docs > *") ||
								document.body.classList.contains("sb-show-errordisplay"),
							null,
							{ timeout: 15_000 },
						)
						.catch(() => {});
					await page.waitForTimeout(Number(args.settle));
					return page.evaluate(readStory);
				};
				let { error: broken } = await load();
				if (broken) {
					console.log(`retry ${story.id} ${mode.name} ${engine} (${broken})`);
					await page.waitForTimeout(3000);
					({ error: broken } = await load());
				}
				if (broken) errors.unshift(`storybook: ${broken}`);
				const touchOn = await page.evaluate(() => document.documentElement.hasAttribute("data-nu-touch"));
				const file = `${story.id}--${mode.name}-${engine}.png`;
				await page.screenshot({ path: path.join(args.out, file), fullPage: false });
				const bad = mode.touch !== touchOn;
				if (bad || errors.length) failed++;
				rows.push({ story: story.id, mode: mode.name, engine, file, touchOn, errors, bad });
				console.log(
					`${bad || errors.length ? "FAIL" : "ok  "} ${story.id} ${mode.name} ${engine}` +
						(bad ? ` (touch mode ${touchOn ? "on" : "off"}, expected ${mode.touch ? "on" : "off"})` : "") +
						(errors.length ? ` (${errors.length} page errors: ${errors[0]})` : ""),
				);
			}
			await ctx.close();
		}
		await browser.close();
	}

	const ids = [...new Set(rows.map((r) => r.story))];
	const cols = [...new Set(rows.map((r) => `${r.mode}-${r.engine}`))];
	const cell = (id, col) => {
		const r = rows.find((x) => x.story === id && `${x.mode}-${x.engine}` === col);
		if (!r) return "<td></td>";
		const note = r.bad || r.errors.length ? `<div class="bad">${r.bad ? "wrong touch mode " : ""}${r.errors.map((e) => e.replace(/</g, "&lt;")).join("<br>")}</div>` : "";
		return `<td><a href="${r.file}"><img src="${r.file}" loading="lazy"></a>${note}</td>`;
	};
	writeFileSync(
		path.join(args.out, "index.html"),
		`<!doctype html><meta charset="utf-8"><title>touch shots</title>
<style>body{font:13px system-ui;margin:16px;background:#f9fafc}table{border-collapse:collapse}td,th{padding:6px;vertical-align:top;text-align:left}
img{width:220px;border:1px solid #d9dadc;border-radius:6px}th{position:sticky;top:0;background:#f9fafc}.bad{color:#d64545;max-width:220px}</style>
<table><tr><th>story</th>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>
${ids.map((id) => `<tr><td>${id}</td>${cols.map((c) => cell(id, c)).join("")}</tr>`).join("\n")}</table>`,
	);
	console.log(`\n${rows.length} shots, ${failed} failed -> ${path.join(args.out, "index.html")}`);
} finally {
	sb.stop();
}
process.exit(failed ? 1 : 0);
