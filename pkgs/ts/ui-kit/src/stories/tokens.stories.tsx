/// <reference types="vite/client" />
// Token pages: every color token, light and dark side by side.
//
// The list is parsed from index.css itself, so a token added there shows up
// here with no edit, grouped by the comment above it. Values resolve in two
// hidden frames that carry this page's stylesheets, one plain (light) and one
// with `.dark` on <html>, so both themes render at once whatever the toolbar
// says. Washes (alpha colors) are drawn over that theme's document ground.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect, useMemo, useState } from "react";
import { Heading } from "../components/ui/heading";
import { Text } from "../components/ui/text";
import css from "../index.css?raw";

type Group = { title: string; vars: string[] };

/** Tokens in `block`, grouped by the comment line above each run. */
function parseGroups(block: string, fallback: string): Group[] {
	const groups: Group[] = [];
	let current: Group = { title: fallback, vars: [] };
	for (const raw of block.split("\n")) {
		const line = raw.trim();
		const comment = line.match(/^\/\*\s*(.*?)(?:\*\/)?$/);
		if (comment && !line.startsWith("/* ===")) {
			if (current.vars.length) groups.push(current);
			const title = comment[1].split(/[:.(]/)[0].trim();
			current = { title: title || fallback, vars: [] };
			continue;
		}
		const decl = line.match(/^--([a-z0-9-]+):\s*(.+);/);
		// colors only: skip geometry (rem, px) tokens
		if (decl && !/\d(rem|px)\b/.test(decl[2]) && !current.vars.includes(decl[1])) {
			current.vars.push(decl[1]);
		}
	}
	if (current.vars.length) groups.push(current);
	return groups;
}

function section(start: string, end: string) {
	const a = css.indexOf(start);
	const b = css.indexOf(end, a + start.length);
	return css.slice(a, b);
}

const LANGUAGE = parseGroups(section(":root {", ".dark {"), "language");

// L2: the shared role block, then the per-theme roles folded into one group.
const ROLES = (() => {
	const shared = parseGroups(section(":root,\n.dark {", "/* ===="), "roles");
	const perTheme = parseGroups(section("L2: light", "L2: dark"), "per theme");
	const seen = new Set(shared.flatMap((g) => g.vars));
	const extra = perTheme.flatMap((g) => g.vars).filter((v) => !seen.has(v));
	return [...shared, { title: "per theme (scrim, hover washes, labels on fills, tree rows)", vars: extra }];
})();

type Resolved = Record<string, { light: string; dark: string; lightGround: string; darkGround: string }>;

/** Resolve every token to rgb(a) in a light and a dark frame. */
function useResolved(key: string) {
	const [values, setValues] = useState<Resolved>({});
	useEffect(() => {
		const names = key.split(" ");
		const frames = ["light", "dark"].map((theme) => {
			const f = document.createElement("iframe");
			f.style.cssText = "position:absolute;width:0;height:0;border:0;visibility:hidden";
			document.body.appendChild(f);
			const doc = f.contentDocument as Document;
			for (const node of document.head.querySelectorAll("style, link[rel=stylesheet]")) {
				doc.head.appendChild(node.cloneNode(true));
			}
			if (theme === "dark") doc.documentElement.classList.add("dark");
			return f;
		});
		const timer = setTimeout(() => {
			const read = (f: HTMLIFrameElement, name: string) => {
				const doc = f.contentDocument as Document;
				const probe = doc.createElement("div");
				probe.style.background = `var(--${name})`;
				doc.body.appendChild(probe);
				const v = getComputedStyle(probe).backgroundColor;
				probe.remove();
				return v;
			};
			const out: Resolved = {};
			for (const n of names) {
				out[n] = {
					light: read(frames[0], n),
					dark: read(frames[1], n),
					lightGround: read(frames[0], "ground-raised"),
					darkGround: read(frames[1], "ground-raised"),
				};
			}
			setValues(out);
		}, 300);
		return () => {
			clearTimeout(timer);
			for (const f of frames) f.remove();
		};
	}, [key]);
	return values;
}

/** oklab(L a b / alpha), what a color-mix computes to, as 0-255 sRGB. */
function oklabToRgb(L: number, a: number, b: number) {
	const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
	const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
	const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
	const lin = [
		4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
		-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
		-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
	];
	return lin.map((x) => {
		const c = Math.min(1, Math.max(0, x));
		return String(Math.round(255 * (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055)));
	});
}

/** rgb()/rgba()/color()/oklab() to #rrggbb, plus alpha % when not opaque. */
function toHex(value: string) {
	if (!value) return "";
	const ok = value.match(/oklab\(([-\d.e]+) ([-\d.e]+) ([-\d.e]+)(?: \/ ([\d.]+))?\)/);
	if (ok) {
		const [r, g, b] = oklabToRgb(Number(ok[1]), Number(ok[2]), Number(ok[3]));
		return toHex(`rgba(${r}, ${g}, ${b}, ${ok[4] ?? 1})`);
	}
	const c = document.createElement("canvas").getContext("2d");
	if (!c) return value;
	c.fillStyle = "#000";
	c.fillStyle = value;
	const s = String(c.fillStyle);
	if (s.startsWith("#")) return s;
	const srgb = s.match(/color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)(?: \/ ([\d.]+))?\)/);
	const m = srgb
		? ["", ...srgb.slice(1, 4).map((x) => String(Math.round(Number(x) * 255))), srgb[4]]
		: s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
	if (!m) return s;
	const hex = `#${[m[1], m[2], m[3]].map((x) => Number(x).toString(16).padStart(2, "0")).join("")}`;
	return m[4] !== undefined && Number(m[4]) < 1 ? `${hex} ${Math.round(Number(m[4]) * 100)}%` : hex;
}

function Chip({ value, ground }: { value: string; ground: string }) {
	return (
		<div className="flex items-center gap-2.5">
			<div className="size-8 shrink-0 rounded-md ring-1 ring-border-subtle ring-inset" style={{ background: ground }}>
				<div className="size-full rounded-md" style={{ background: value }} />
			</div>
			<span className="font-mono text-[11px] text-text-secondary">{toHex(value)}</span>
		</div>
	);
}

function Table({ groups }: { groups: Group[] }) {
	const key = useMemo(() => groups.flatMap((g) => g.vars).join(" "), [groups]);
	const values = useResolved(key);
	return (
		<div className="space-y-8">
			{groups.map((g) => (
				<section key={g.title}>
					<Heading as="h2" size="lg" className="mb-2">
						{g.title}
					</Heading>
					<div className="overflow-hidden rounded-lg border border-border-subtle">
						<div className="grid grid-cols-[1.3fr_1fr_1fr] bg-bg-sunken px-4 py-2 text-xs font-medium text-text-muted">
							<span>token</span>
							<span>light</span>
							<span>dark</span>
						</div>
						{g.vars.map((v) => {
							const r = values[v];
							return (
								<div
									key={v}
									className="grid grid-cols-[1.3fr_1fr_1fr] items-center border-t border-border-subtle px-4 py-2"
								>
									<span className="font-mono text-xs text-text-primary">{v}</span>
									{r ? <Chip value={r.light} ground={r.lightGround} /> : <span />}
									{r ? <Chip value={r.dark} ground={r.darkGround} /> : <span />}
								</div>
							);
						})}
					</div>
				</section>
			))}
		</div>
	);
}

export const Language: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
			<Heading as="h1" size="3xl" className="mb-2">
				L1 language tokens
			</Heading>
			<Text size="sm" tone="secondary" className="mb-10">
				Every value in the color language, Dawn (light) and Dusk (dark) side by side. Components
				never use these directly; they go through the L2 roles.
			</Text>
			<Table groups={LANGUAGE} />
		</div>
	),
};

export const Roles: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
			<Heading as="h1" size="3xl" className="mb-2">
				L2 kit roles
			</Heading>
			<Text size="sm" tone="secondary" className="mb-10">
				The names components use, resolved in both themes. Washes are drawn over the document
				ground.
			</Text>
			<Table groups={ROLES} />
		</div>
	),
};

const meta: Meta = {
	title: "Docs/Tokens",
};

export default meta;
