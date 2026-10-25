// Refs/Page: the parts a page is made of, as a program draws them. A titled
// PageSection with actions in its header, a sidebar and a top bar of nav
// items, a feature list of framed icons, pages linked as rows, as tiles and
// inline as mentions, a Spacer pushing a toolbar's end, and a page capped
// and centered by its Column.

import type { ChainStep } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Page",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

/** Each child chain under `parent`, root-first. */
function under(parent: ChainStep[], ...children: ChainStep[][]): ChainStep[][] {
	return children.map((c) => [...parent, ...c]);
}

function statCard(segment: string, title: string, label: string, value: string, delta: string) {
	return [
		[step(segment, "Card", { title })],
		[step(segment, "Card"), step("stat", "StatRef", { label, value, delta, trend: "up" })],
	];
}

export const SectionWithActions: Story = {
	render: () => {
		const root = "page-section";
		const sec = [
			step(root, "PageSection", {
				title: "Usage",
				description: "Runs, tokens and errors over the last 30 days.",
				size: "md",
				bordered: false,
				gap: 4,
			}),
		];
		const actions = [...sec, step("actions", "Row", { gap: 2 })];
		const grid = [...sec, step("stats", "Grid", { columns: 3, min_width: 180, gap: 3 })];
		return (
			<NodeStage
				root={root}
				label="Section: title, description, a Row of buttons at `actions`, a Grid body"
				chains={[
					sec,
					...under(
						actions,
						[step("range", "ButtonRef", { label: "30 days", variant: "ghost" })],
						[
							step("export", "ButtonRef", {
								label: "Export",
								variant: "secondary",
								icon: "download",
							}),
						],
					),
					...under(
						grid,
						...statCard("runs", "Runs", "today", "1,284", "+ 12%"),
						...statCard("tokens", "Tokens", "today", "842k", "+ 3%"),
						...statCard("errors", "Errors", "today", "0.9%", "- 0.2 pp"),
					),
				]}
			/>
		);
	},
};

export const Sidebar: Story = {
	render: () => {
		const root = "page-sidebar";
		const col = [step(root, "Column", { gap: 2, max_width: "form", center: false })];
		const main = [...col, step("main", "NavList", { label: "Workspace" })];
		const more = [...col, step("more", "NavList", { label: "Library" })];
		const item = (seg: string, label: string, href: string, icon: string, extra = {}) => [
			step(seg, "NavItemRef", {
				label,
				href,
				icon,
				meta: "",
				active: null,
				exact: false,
				...extra,
			}),
		];
		return (
			<NodeStage
				root={root}
				label="two vertical NavLists in a capped Column; Docs pinned active, the rest follow the tab"
				chains={[
					...under(
						main,
						item("home", "Home", "/", "home", { exact: true }),
						item("docs", "Docs", "/docs", "book-open", { active: true }),
						item("runs", "Runs", "/runs", "activity", { meta: "12" }),
						item("inbox", "Inbox", "/inbox", "inbox", { meta: "3" }),
					),
					...under(
						more,
						item("data", "Datasets", "/data", "database"),
						item("models", "Models", "/models", "brain"),
						item("settings", "Settings", "/settings", "settings"),
					),
				]}
			/>
		);
	},
};

export const TopBar: Story = {
	render: () => {
		const root = "page-topbar";
		const bar = [step(root, "Row", { gap: 3, align: "center", padding: 2 })];
		const nav = [...bar, step("nav", "NavList", { variant: "horizontal", label: "Main" })];
		const item = (seg: string, label: string, href: string, active: boolean | null) => [
			step(seg, "NavItemRef", { label, href, active }),
		];
		return (
			<NodeStage
				root={root}
				label="Row: icon, title, a horizontal NavList, a Spacer, then the button at the end"
				chains={[
					...under(
						bar,
						[step("logo", "IconRef", { name: "layers", size: "lg", tone: "accent" })],
						[step("name", "TextRef", { value: "Atlas", weight: "semibold" })],
					),
					...under(
						nav,
						item("overview", "Overview", "/overview", true),
						item("runs", "Runs", "/runs", false),
						item("docs", "Docs", "/docs", false),
					),
					...under(
						bar,
						[step("push", "SpacerRef")],
						[step("new", "ButtonRef", { label: "New run", icon: "plus" })],
					),
				]}
			/>
		);
	},
};

const FEATURES = [
	[
		"rocket",
		"accent",
		"Ships in one call",
		"One Python program, served to the browser as it runs.",
	],
	[
		"shield-check",
		"ok",
		"Safe by default",
		"Nothing reaches the page that the program did not write.",
	],
	["workflow", "info", "Composable", "Rows, grids and sections nest like the data they show."],
	["gauge", "warn", "Fast on the wire", "A write carries its chain; nothing waits on a boot."],
] as const;

export const FeatureList: Story = {
	render: () => {
		const root = "page-features";
		const grid = [step(root, "Grid", { columns: 2, min_width: 220, gap: 6, align: "start" })];
		const chains = FEATURES.flatMap(([icon, tone, title, body], i) => {
			const row = [...grid, step(`f${i}`, "Row", { gap: 3, align: "start" })];
			const text = [...row, step("text", "Column", { gap: 1 })];
			return [
				[...row, step("icon", "IconRef", { name: icon, tone, framed: true })],
				[...text, step("title", "TextRef", { value: title, weight: "medium" })],
				[...text, step("body", "TextRef", { value: body, tone: "secondary", size: "sm" })],
			];
		});
		return (
			<NodeStage
				root={root}
				label="Grid of Rows: a framed IconRef beside a title and a line"
				chains={chains}
			/>
		);
	},
};

export const IconInLine: Story = {
	render: () => {
		const root = "page-icon-line";
		const line = [step(root, "Line")];
		return (
			<NodeStage
				root={root}
				label="IconRef in a Line: text sized, on the baseline"
				chains={under(
					line,
					[step("a", "TextRef", { value: "All checks" })],
					[step("ok", "IconRef", { name: "circle-check", tone: "ok", label: "passed" })],
					[step("b", "TextRef", { value: "passed on main, see" })],
					[step("c", "LinkRef", { href: "#", label: "the run" })],
				)}
			/>
		);
	},
};

const PAGES = [
	["📝", "Meeting notes", "Weekly sync, decisions and follow-ups", "2d ago"],
	["book-open", "Field guide", "How the team names, ships and reviews", "Gor"],
	["🗺️", "Roadmap", "What lands this quarter and why", "12 items"],
	["database", "Datasets", "Every table the models train on", ""],
] as const;

function pageLink(i: number, variant: "row" | "tile" | "inline"): ChainStep[] {
	const [icon, title, description, meta] = PAGES[i];
	return [
		step(`p${i}`, "PageLinkRef", {
			href: `#${title.toLowerCase().replace(/ /g, "-")}`,
			title,
			icon,
			description,
			meta,
			variant,
			target: "_self",
		}),
	];
}

export const PageLinkRows: Story = {
	render: () => {
		const root = "page-links-rows";
		const list = [step(root, "Column", { gap: 0 })];
		return (
			<NodeStage
				root={root}
				label="PageLinkRef rows: emoji or icon mark, title, a line, a trailing note"
				chains={under(list, ...PAGES.map((_, i) => pageLink(i, "row")))}
			/>
		);
	},
};

export const PageLinkTiles: Story = {
	render: () => {
		const root = "page-links-tiles";
		const grid = [step(root, "Grid", { columns: 4, min_width: 160, gap: 3 })];
		return (
			<NodeStage
				root={root}
				label="PageLinkRef tiles in a Grid"
				chains={under(grid, ...PAGES.map((_, i) => pageLink(i, "tile")))}
			/>
		);
	},
};

export const PageLinkInline: Story = {
	render: () => {
		const root = "page-links-inline";
		const col = [step(root, "Column", { gap: 2 })];
		const line = [...col, step("line", "Line")];
		const run = (seg: string, value: string): ChainStep[] => [step(seg, "TextRef", { value })];
		return (
			<NodeStage
				root={root}
				label="PageLinkRef inline: a mention on its own line, and in a Line with the text"
				chains={[
					...under(col, pageLink(0, "inline"), pageLink(1, "inline")),
					...under(
						line,
						run("a", "Before the review, read"),
						pageLink(2, "inline"),
						run("b", "and check the numbers in"),
						pageLink(3, "inline"),
						run("c", "so the plan and the data agree."),
					),
				]}
			/>
		);
	},
};

export const CenteredPage: Story = {
	render: () => {
		const root = "page-centered";
		const page = [step(root, "Column", { gap: 6, padding: 4, max_width: "form", center: true })];
		const head = [...page, step("head", "Row", { gap: 3, align: "center" })];
		const about = [
			...page,
			step("about", "PageSection", { title: "About", description: "What this page is for." }),
		];
		const pages = [...page, step("pages", "PageSection", { title: "Pages", bordered: true })];
		return (
			<NodeStage
				root={root}
				label="Column(max_width='form'): a 480px page centered in its column"
				chains={[
					...under(
						head,
						[
							step("icon", "IconRef", {
								name: "compass",
								size: "xl",
								tone: "accent",
								framed: true,
							}),
						],
						[step("title", "TextRef", { value: "Team space", size: "xl", weight: "semibold" })],
						[step("push", "SpacerRef")],
						[step("share", "ButtonRef", { label: "Share", variant: "secondary", icon: "share-2" })],
					),
					[
						...about,
						step("body", "TextRef", {
							value:
								"Notes, plans and the field guide, one link each. Pin the ones you open daily.",
							tone: "secondary",
						}),
					],
					...under(
						pages,
						...PAGES.slice(0, 3).map(([icon, title, description, meta], i) => [
							step(`p${i}`, "PageLinkRef", { href: "#", title, icon, description, meta }),
						]),
					),
				]}
			/>
		);
	},
};
