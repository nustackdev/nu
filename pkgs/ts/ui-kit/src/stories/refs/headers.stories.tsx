// Refs/Headers: every container with chrome, headed two ways, as a program
// draws it. On the left of each pair the string shorthand (`title`, an
// accordion section's `label`, a popover's trigger `label`); on the right a
// `header` child in its place: a Row of a status dot, a name that grows and
// cuts to one line, a badge and an icon button. Card and PageSection keep
// the button on their `actions` rail, the way they want it; the rest hold it
// in the header Row. Then the same Rows at a narrow width, the long name
// cut with an ellipsis while the dot, badge and button keep their size.
// Modal, Sheet and Popover portal to <body>, so each renders alone in a
// hidden story that the Matrix frames once per theme.

import type { ChainStep } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { FramePair, NodeSolo, NodeStage, SinkPage, sinkParameters, step } from "./harness";

// The light pin rides the visible story, not the meta, so a hidden pane
// takes the theme its frame asks for.
const meta: Meta = {
	title: "Refs/Headers",
	parameters: { layout: "fullscreen" },
};

export default meta;

type Story = StoryObj;
type Chain = ChainStep[];

const LONG = "web-03.eu-central.cluster.internal, rebuilt from main";

const more = (seg = "more") =>
	step(seg, "ButtonRef", {
		label: "",
		icon: "ellipsis",
		tooltip: "More",
		variant: "ghost",
		size: "sm",
	});

/**
 * A header Row at `seg` under `prefix`: a status dot, a name that grows and
 * cuts to one line, a badge, and an icon button unless it sits on a rail.
 */
function header(
	prefix: Chain,
	seg: string,
	{
		name,
		tone = "ok",
		badge = "healthy",
		variant = "ok",
		button = true,
		size = "base",
		weight = "medium",
	}: {
		name: string;
		tone?: string;
		badge?: string;
		variant?: string;
		button?: boolean;
		size?: string;
		weight?: string;
	},
): Chain[] {
	const row = [...prefix, step(seg, "Row", { gap: 2, grow: { name: 1 } })];
	return [
		[...row, step("dot", "StatusDotRef", { tone })],
		[...row, step("name", "TextRef", { value: name, lines: 1, size, weight })],
		[...row, step("badge", "BadgeRef", { label: badge, variant })],
		...(button ? [[...row, more()]] : []),
	];
}

const body = (prefix: Chain, value: string) => [
	...prefix,
	step("body", "TextRef", { value, tone: "secondary", size: "sm" }),
];

// One pair per container: a caption, then a two cell grid, string on the left.
function pair(root: Chain, seg: string, caption: string): [Chain, Chain, Chain] {
	const group = [...root, step(seg, "Column", { gap: 2 })];
	const grid = [...group, step("grid", "Grid", { max_columns: 2, min_cell_width: 240, gap: 4 })];
	return [
		[
			...group,
			step("caption", "TextRef", { value: caption, size: "xs", tone: "muted", mono: true }),
		],
		grid,
		group,
	];
}

function inlineChains(rootSeg: string): Chain[] {
	const root = [step(rootSeg, "Column", { gap: 8 })];
	const chains: Chain[] = [];

	// Card: title + subtitle, then a header Row with the button on `actions`.
	{
		const [cap, grid] = pair(root, "card", "Card: title + subtitle | header Row, actions rail");
		const plain = [...grid, step("plain", "Card", { title: "web-03", subtitle: "eu-central" })];
		const rich = [...grid, step("rich", "Card")];
		chains.push(
			cap,
			[
				...plain,
				step("actions", "ButtonRef", {
					label: "",
					icon: "ellipsis",
					tooltip: "More",
					variant: "ghost",
					size: "sm",
				}),
			],
			body(plain, "4 vCPU, 16 GB, up 12 days."),
			...header(rich, "header", { name: "web-03", button: false }),
			[...rich, more("actions")],
			body(rich, "4 vCPU, 16 GB, up 12 days."),
		);
	}

	// PageSection: title + description, then a header Row, actions kept.
	{
		const [cap, grid] = pair(
			root,
			"section",
			"PageSection: title + description | header Row, actions",
		);
		const plain = [
			...grid,
			step("plain", "PageSection", {
				title: "Hosts",
				description: "Every machine in the cluster.",
			}),
		];
		const rich = [...grid, step("rich", "PageSection")];
		chains.push(
			cap,
			[...plain, step("actions", "ButtonRef", { label: "Add", icon: "plus", size: "sm" })],
			body(plain, "12 hosts across two regions."),
			...header(rich, "header", {
				name: "Hosts in eu-central",
				badge: "12",
				variant: "neutral",
				button: false,
				size: "xl",
				weight: "semibold",
			}),
			[...rich, step("actions", "ButtonRef", { label: "Add", icon: "plus", size: "sm" })],
			body(rich, "12 hosts across two regions."),
		);
	}

	// Collapsible: title, then a header Row as the trigger row. The button
	// in it does not toggle; a click on the name does.
	{
		const [cap, grid] = pair(
			root,
			"collapsible",
			"Collapsible: title | header Row (button does not toggle)",
		);
		const plain = [...grid, step("plain", "Collapsible", { title: "Deploy details", open: true })];
		const rich = [...grid, step("rich", "Collapsible", { open: true })];
		chains.push(
			cap,
			body(plain, "Last deploy 12 minutes ago."),
			...header(rich, "header", {
				name: "Deploy web-03",
				tone: "warn",
				badge: "running",
				variant: "warn",
			}),
			body(rich, "Last deploy 12 minutes ago."),
		);
	}

	// Accordion: plain labels, then two sections headed by different Rows
	// and a third keeping its string label.
	{
		const [cap, grid] = pair(
			root,
			"accordion",
			"Accordion: labels | header:<id> on two sections, the third a string label",
		);
		const sections = [
			{ id: "build", label: "Build" },
			{ id: "deploy", label: "Deploy" },
			{ id: "notes", label: "Notes" },
		];
		const plain = [...grid, step("plain", "Accordion", { sections, open: ["build"] })];
		const rich = [...grid, step("rich", "Accordion", { sections, open: ["build"] })];
		chains.push(
			cap,
			[...plain, step("build", "TextRef", { value: "Built in 42s.", size: "sm" })],
			[...plain, step("deploy", "TextRef", { value: "Not deployed yet.", size: "sm" })],
			[...plain, step("notes", "TextRef", { value: "Nothing to add.", size: "sm" })],
			...header(rich, "header:build", { name: "Build web-03", badge: "passed" }),
			...header(rich, "header:deploy", {
				name: "Deploy to eu-central",
				tone: "neutral",
				badge: "queued",
				variant: "neutral",
			}),
			[...rich, step("build", "TextRef", { value: "Built in 42s.", size: "sm" })],
			[...rich, step("deploy", "TextRef", { value: "Not deployed yet.", size: "sm" })],
			[...rich, step("notes", "TextRef", { value: "Nothing to add.", size: "sm" })],
		);
	}

	// Quote: title, then a header Row.
	{
		const [cap, grid] = pair(root, "quote", "Quote: title | header Row");
		const plain = [...grid, step("plain", "Quote", { title: "Note" })];
		const rich = [...grid, step("rich", "Quote")];
		chains.push(
			cap,
			[...plain, step("body", "TextRef", { value: "Changes apply on the next deploy." })],
			...header(rich, "header", {
				name: "Working",
				tone: "info",
				badge: "12s",
				variant: "neutral",
			}),
			[
				...rich,
				step("body", "TextRef", { value: "Read the deploy config and the last three runs." }),
			],
		);
	}

	// Narrow: the same Rows in 220px cells, the long name cut with an ellipsis.
	{
		const group = [...root, step("narrow", "Column", { gap: 2 })];
		const grid = [...group, step("grid", "Grid", { max_columns: 3, min_cell_width: 180, gap: 4 })];
		const card = [...grid, step("card", "Card", { max_width: 220 })];
		const section = [...grid, step("section", "PageSection", { max_width: 220 })];
		const col = [...grid, step("collapsible", "Collapsible", { open: false, max_width: 220 })];
		const acc = [
			...grid,
			step("accordion", "Accordion", {
				sections: [{ id: "a", label: "A string label far too long for its row" }],
				max_width: 220,
			}),
		];
		const quote = [...grid, step("quote", "Quote", { max_width: 220 })];
		chains.push(
			[
				...group,
				step("caption", "TextRef", {
					value: "Narrow (220px): the name cuts, the dot, badge and buttons stay put",
					size: "xs",
					tone: "muted",
					mono: true,
				}),
			],
			...header(card, "header", { name: LONG, button: false }),
			[...card, more("actions")],
			body(card, "The body wraps as usual."),
			...header(section, "header", { name: LONG, button: false }),
			[...section, more("actions")],
			body(section, "The body wraps as usual."),
			...header(col, "header", { name: LONG, tone: "warn", badge: "running", variant: "warn" }),
			body(col, "Folded away."),
			...header(acc, "header:a", { name: LONG }),
			[...acc, step("a", "TextRef", { value: "Folded away.", size: "sm" })],
			...header(quote, "header", { name: LONG, tone: "info", badge: "3m", variant: "neutral" }),
			body(quote, "The body wraps as usual."),
		);
	}

	return chains;
}

// Hidden: a modal titled by its string.
export const ModalTitlePane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = [step("headers-modal-title", "Column", { gap: 3 })];
		const modal = [
			...col,
			step("modal", "Modal", { title: "Deploy web-03", open: true, width: 420 }),
		];
		return (
			<NodeSolo
				root="headers-modal-title"
				chains={[
					[...col, step("heading", "HeadingRef", { label: "Deploys" })],
					[...modal, step("note", "TextRef", { value: "Rolls out to 4 hosts, one at a time." })],
					[...modal, step("go", "ButtonRef", { label: "Deploy" })],
				]}
			/>
		);
	},
};

// Hidden: the same modal headed by a Row, the close button kept beside it.
export const ModalHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = [step("headers-modal-header", "Column", { gap: 3 })];
		const modal = [...col, step("modal", "Modal", { open: true, width: 420 })];
		return (
			<NodeSolo
				root="headers-modal-header"
				chains={[
					[...col, step("heading", "HeadingRef", { label: "Deploys" })],
					...header(modal, "header", {
						name: LONG,
						tone: "warn",
						badge: "prod",
						variant: "warn",
						size: "lg",
						weight: "semibold",
					}),
					[...modal, step("note", "TextRef", { value: "Rolls out to 4 hosts, one at a time." })],
					[...modal, step("go", "ButtonRef", { label: "Deploy" })],
				]}
			/>
		);
	},
};

// Hidden: a sheet titled by its string.
export const SheetTitlePane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = [step("headers-sheet-title", "Column", { gap: 3 })];
		const sheet = [
			...col,
			step("sheet", "Sheet", { title: "web-03", open: true, side: "right", width: 320 }),
		];
		return (
			<NodeSolo
				root="headers-sheet-title"
				chains={[
					[...col, step("heading", "HeadingRef", { label: "Hosts" })],
					body(sheet, "4 vCPU, 16 GB, up 12 days."),
				]}
			/>
		);
	},
};

// Hidden: the same sheet headed by a Row, the long name cut to one line.
export const SheetHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const col = [step("headers-sheet-header", "Column", { gap: 3 })];
		const sheet = [...col, step("sheet", "Sheet", { open: true, side: "right", width: 320 })];
		return (
			<NodeSolo
				root="headers-sheet-header"
				chains={[
					[...col, step("heading", "HeadingRef", { label: "Hosts" })],
					...header(sheet, "header", {
						name: LONG,
						badge: "primary",
						variant: "neutral",
						size: "lg",
						weight: "semibold",
					}),
					body(sheet, "4 vCPU, 16 GB, up 12 days."),
				]}
			/>
		);
	},
};

// Hidden: a popover with a string trigger label and a string panel title.
export const PopoverTitlePane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const row = [step("headers-popover-title", "Row", { gap: 3, justify: "end" })];
		const pop = [
			...row,
			step("pop", "Popover", {
				label: "web-03",
				icon: "server",
				variant: "secondary",
				title: "web-03",
				open: true,
				width: 280,
			}),
		];
		return (
			<NodeSolo
				root="headers-popover-title"
				chains={[
					body(pop, "4 vCPU, 16 GB, up 12 days."),
					[...pop, step("open", "ButtonRef", { label: "Open host", variant: "ghost" })],
				]}
			/>
		);
	},
};

// Hidden: the same popover, a Row at `trigger` (dot and name in one button)
// and a Row at `header` heading the panel.
export const PopoverHeaderPane: Story = {
	tags: ["!dev", "!autodocs"],
	render: () => {
		const row = [step("headers-popover-header", "Row", { gap: 3, justify: "end" })];
		const pop = [
			...row,
			step("pop", "Popover", { tooltip: "web-03", variant: "secondary", open: true, width: 280 }),
		];
		const trigger = [...pop, step("trigger", "Row", { gap: 2 })];
		return (
			<NodeSolo
				root="headers-popover-header"
				chains={[
					[...trigger, step("dot", "StatusDotRef", { tone: "ok" })],
					[...trigger, step("name", "TextRef", { value: "web-03", size: "sm" })],
					...header(pop, "header", { name: LONG }),
					body(pop, "4 vCPU, 16 GB, up 12 days."),
					[...pop, step("open", "ButtonRef", { label: "Open host", variant: "ghost" })],
				]}
			/>
		);
	},
};

const OVERLAYS = [
	["modal-title-pane", "Modal: title", 340],
	["modal-header-pane", "Modal: header Row, close kept", 340],
	["sheet-title-pane", "Sheet: title", 260],
	["sheet-header-pane", "Sheet: header Row, long name cut", 260],
	["popover-title-pane", "Popover: trigger label + title", 260],
	["popover-header-pane", "Popover: trigger Row + header Row", 260],
] as const;

export const Matrix: Story = {
	parameters: sinkParameters,
	render: () => (
		<SinkPage
			title="Headers"
			description="Every container with chrome: the string title on the left, a header Row in its place on the right. Then a narrow row, and the overlays framed once per theme."
		>
			<NodeStage root="headers-inline" chains={inlineChains("headers-inline")} />
			<div className="flex flex-col gap-6 py-6">
				{OVERLAYS.map(([id, label, height]) => (
					<FramePair key={id} storyId={`refs-headers--${id}`} label={label} height={height} />
				))}
			</div>
		</SinkPage>
	),
};
