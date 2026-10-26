// Refs/Looks: the looks a page is built from, as a program draws them. Text
// tones, sizes and clamps; heading sizes with an eyebrow and a subtitle;
// button looks, sizes and button links; link variants inline in a Line; card
// surfaces, a link card, a media card and a grid of plan cards whose footer
// actions line up at the bottom; tabs strips, empty states, brand badges and
// box grounds.

import type { ChainStep } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { TONES } from "../../lib/recipes";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Looks",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

/** One chain per child, each under `parent` (itself root-first). */
function under(parent: ChainStep[], children: ChainStep[]): ChainStep[][] {
	return [parent, ...children.map((c) => [...parent, c])];
}

// A stand-in photo, inline so the story draws offline.
const BANNER = `data:image/svg+xml;utf8,${encodeURIComponent(
	'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 90"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5cd6"/><stop offset="1" stop-color="#e0915a"/></linearGradient></defs><rect width="160" height="90" fill="url(#g)"/></svg>',
)}`;

const LONG =
	"A cell is one Python program with its own page. It runs on the cluster, streams its state to the tab and keeps going when the tab closes, so a long job is a page you come back to rather than a terminal you babysit.";

export const Type: Story = {
	render: () => {
		const col = [step("looks-type", "Column", { gap: 3 })];
		return (
			<NodeStage
				root="looks-type"
				label="TextRef tone / size / weight / mono / align / lines; HeadingRef size, eyebrow, subtitle"
				chains={under(col, [
					step("hero", "HeadingRef", {
						label: "Programs that are pages",
						level: 1,
						size: "display",
						eyebrow: "Nu 0.6",
						subtitle: "Write the model once; the tab, the cluster and the store follow.",
					}),
					step("centered", "HeadingRef", {
						label: "Centered section",
						level: 2,
						align: "center",
						subtitle: "align start / center / end, left / right still read",
					}),
					step("quiet", "HeadingRef", { label: "A secondary h3", level: 3, tone: "secondary" }),
					...TONES.map((t) => step(`t-${t}`, "TextRef", { value: `tone ${t}`, tone: t })),
					step("small", "TextRef", { value: "size xs, medium", size: "xs", weight: "medium" }),
					step("large", "TextRef", { value: "size xl, semibold", size: "xl", weight: "semibold" }),
					step("mono", "TextRef", {
						value: "nu.run(cell) -> 0.42s",
						mono: true,
						tone: "secondary",
					}),
					step("mid", "TextRef", { value: "centered paragraph", align: "center" }),
					step("one", "TextRef", { value: LONG, lines: 1, tone: "secondary" }),
					step("two", "TextRef", { value: LONG, lines: 2 }),
				])}
			/>
		);
	},
};

const BUTTON_LOOKS = [
	"primary",
	"secondary",
	"outline",
	"ghost",
	"soft",
	"danger",
	"link",
] as const;
const SIZES = ["xs", "sm", "md", "lg"] as const;

export const Actions: Story = {
	render: () => {
		const col = [step("looks-actions", "Column", { gap: 4 })];
		const row = (seg: string) => [...col, step(seg, "Row", { gap: 2, wrap: true })];
		const line = [...col, step("prose", "Line", {})];
		return (
			<NodeStage
				root="looks-actions"
				label="ButtonRef variants and sizes, href buttons (the button-look link); LinkRef text / muted"
				chains={[
					col,
					...under(
						row("looks"),
						BUTTON_LOOKS.map((v) => step(`b-${v}`, "ButtonRef", { label: v, variant: v })),
					),
					...under(
						row("sizes"),
						SIZES.flatMap((s) => [
							step(`s-${s}`, "ButtonRef", { label: `size ${s}`, size: s, variant: "secondary" }),
							step(`i-${s}`, "ButtonRef", {
								label: "",
								icon: "settings",
								size: s,
								variant: "ghost",
								tooltip: `icon ${s}`,
							}),
						]),
					),
					...under(row("hrefs"), [
						step("start", "ButtonRef", { label: "Get started", href: "#start", icon: "sparkles" }),
						step("plans", "ButtonRef", {
							label: "See plans",
							href: "#plans",
							variant: "secondary",
						}),
						step("docs", "ButtonRef", {
							label: "Docs",
							href: "https://nustack.dev",
							target: "_blank",
							variant: "outline",
						}),
					]),
					...under(row("links"), [
						step("l-icon", "LinkRef", { href: "#c", label: "Notes", icon: "file-text" }),
						step("l-text", "LinkRef", { href: "#d", label: "Read more", arrow: true }),
						step("l-muted", "LinkRef", { href: "#e", label: "Changelog", variant: "muted" }),
					]),
					line,
					[...line, step("0", "TextRef", { value: "Inline, a" })],
					[...line, step("1", "LinkRef", { href: "#x", label: "text link" })],
					[...line, step("2", "TextRef", { value: "and a" })],
					[...line, step("3", "LinkRef", { href: "#y", label: "muted one", variant: "muted" })],
					[...line, step("4", "TextRef", { value: "wrap with the sentence;", tone: "secondary" })],
					[...line, step("5", "TextRef", { value: "v0.6.6", mono: true })],
				]}
			/>
		);
	},
};

const PLANS = [
	{ id: "free", title: "Free", price: "$0", lines: ["One cell", "Community support"] },
	{
		id: "pro",
		title: "Pro",
		price: "$9",
		lines: ["Ten cells", "Cluster runs", "Store snapshots", "Email support"],
		popular: true,
	},
	{ id: "team", title: "Team", price: "$29", lines: ["Unlimited cells", "Shared planes"] },
];

export const Cards: Story = {
	render: () => {
		const col = [step("looks-cards", "Column", { gap: 4 })];
		const grid = [...col, step("plans", "Grid", { columns: 3, gap: 3 })];
		const chains: ChainStep[][] = [col, grid];
		for (const p of PLANS) {
			const card = [
				...grid,
				step(p.id, "Card", {
					title: p.title,
					subtitle: "per month",
					variant: p.popular ? "elevated" : "default",
				}),
			];
			chains.push(card);
			if (p.popular)
				chains.push([...card, step("actions", "BadgeRef", { label: "Popular", variant: "brand" })]);
			chains.push([
				...card,
				step("price", "HeadingRef", { label: p.price, level: 3, size: "3xl" }),
			]);
			p.lines.forEach((l, i) => {
				chains.push([
					...card,
					step(`f${i}`, "TextRef", { value: l, tone: "secondary", size: "sm" }),
				]);
			});
			chains.push([
				...card,
				step("footer", "ButtonRef", {
					label: `Choose ${p.title}`,
					variant: p.popular ? "primary" : "secondary",
					href: `#${p.id}`,
				}),
			]);
		}
		const surfaces = [...col, step("surfaces", "Grid", { columns: 4, gap: 3 })];
		for (const v of ["default", "elevated", "sunken", "outline"]) {
			const card = [...surfaces, step(v, "Card", { title: v, variant: v, size: "sm" })];
			chains.push(card, [...card, step("t", "TextRef", { value: "size sm", tone: "muted" })]);
		}
		const more = [...col, step("more", "Grid", { columns: 2, gap: 3 })];
		const media = [...more, step("media", "Card", { title: "Release notes", subtitle: "0.6.6" })];
		chains.push(
			media,
			[...media, step("media", "ImageRef", { src: BANNER, alt: "", aspect: "16/9", fit: "cover" })],
			[...media, step("t", "TextRef", { value: LONG, lines: 2, tone: "secondary" })],
			[
				...media,
				step("footer", "LinkRef", { href: "#notes", label: "Read the notes", arrow: true }),
			],
		);
		const link = [
			...more,
			step("link", "Card", {
				title: "Docs",
				subtitle: "The whole card is one link",
				href: "#docs",
				caption: "nustack.dev/docs",
			}),
		];
		chains.push(link, [
			...link,
			step("t", "TextRef", { value: LONG, lines: 3, tone: "secondary" }),
		]);
		return (
			<NodeStage
				root="looks-cards"
				label="Card media / action / footer slots, variants, href; footers line up across a stretched grid row"
				chains={chains}
			/>
		);
	},
};

export const Chrome: Story = {
	render: () => {
		const col = [step("looks-chrome", "Column", { gap: 4 })];
		const tabs = [
			{ id: "a", label: "Overview" },
			{ id: "b", label: "Runs" },
			{ id: "c", label: "Settings" },
		];
		const chains: ChainStep[][] = [col];
		for (const v of ["line", "pill", "segmented"]) {
			const t = [...col, step(`tabs-${v}`, "Tabs", { tabs, active: "a", variant: v })];
			chains.push(t, [...t, step("a", "TextRef", { value: `${v} tabs`, tone: "muted" })]);
		}
		const badges = [...col, step("badges", "Row", { gap: 2, wrap: true })];
		chains.push(
			...under(badges, [
				step("brand", "BadgeRef", { label: "brand", variant: "brand" }),
				step("secondary", "BadgeRef", { label: "secondary", variant: "secondary" }),
				step("neutral", "BadgeRef", { label: "neutral" }),
				step("sm", "BadgeRef", { label: "sm", variant: "ok", size: "sm" }),
				step("lg", "BadgeRef", { label: "lg", variant: "info", size: "lg" }),
			]),
		);
		const grounds = [...col, step("grounds", "Grid", { columns: 5, gap: 3 })];
		for (const g of ["none", "muted", "sunken", "accent", "brand"]) {
			const box = [...grounds, step(g, "Box", { background: g, title: g })];
			chains.push(box, [...box, step("t", "TextRef", { value: "Box ground", size: "sm" })]);
		}
		const flush = [...col, step("flush", "Box", { padding: "none", background: "sunken" })];
		chains.push(flush, [
			...flush,
			step("t", "TextRef", { value: "padding none: flush to the edge" }),
		]);
		const empties = [...col, step("empties", "Grid", { columns: 2, gap: 3 })];
		chains.push(
			...under(empties, [
				step("e1", "EmptyStateRef", {
					label: "No planes yet",
					description: "A plane groups the cells of one project.",
					icon: "folder",
					action: "New plane",
				}),
				step("e2", "EmptyStateRef", {
					label: "Nothing matches",
					icon: "search",
					action: "Read the search docs",
					action_href: "#docs",
					size: "sm",
				}),
			]),
		);
		chains.push([
			...col,
			step("rule", "DividerRef", { label: "start-aligned label", align: "start" }),
		]);
		return (
			<NodeStage
				root="looks-chrome"
				label="Tabs variants, Badge brand tones and sizes, Box grounds, EmptyState icon + action, Divider align"
				chains={chains}
			/>
		);
	},
};
