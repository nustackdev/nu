// Nodes/Display: the display leaves as a program draws them. Avatar,
// Breadcrumb, Skeleton, Spinner and StatusPill in every size and tone,
// inside a Column, a Row and a Card, so the parent's flow is what places
// each one.

import type { ChainStep } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Nodes/Display",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

// A stand-in photo, inline so the story draws offline.
const PHOTO = `data:image/svg+xml;utf8,${encodeURIComponent(
	'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5cd6"/><stop offset="1" stop-color="#e0915a"/></linearGradient></defs><rect width="64" height="64" fill="url(#g)"/><circle cx="32" cy="26" r="11" fill="#fff" fill-opacity=".85"/><path d="M12 60c3-12 11-18 20-18s17 6 20 18z" fill="#fff" fill-opacity=".85"/></svg>',
)}`;

const SIZES = ["sm", "md", "lg", "xl"] as const;
const TONES = ["neutral", "info", "ok", "warn", "danger"] as const;
const PILL_LABEL: Record<(typeof TONES)[number], string> = {
	neutral: "Idle",
	info: "Syncing",
	ok: "Deployed",
	warn: "Degraded",
	danger: "Failed",
};

const TRAIL = [
	{ label: "Home", href: "/" },
	{ label: "Planes", href: "/planes" },
	{ label: "Docs", href: "https://nustack.dev/docs" },
	{ label: "rivendell", href: "" },
];

/** One chain per child, each under `parent` (itself root-first). */
function under(parent: ChainStep[], children: ChainStep[]): ChainStep[][] {
	return [parent, ...children.map((c) => [...parent, c])];
}

export const InColumn: Story = {
	render: () => {
		const col = [step("display-column", "Column", { gap: 4 })];
		const row = (seg: string) => [...col, step(seg, "Row", { gap: 3 })];
		return (
			<NodeStage
				root="display-column"
				label="block flow: each leaf on its own line, rows of sizes and tones"
				chains={[
					col,
					[...col, step("trail", "BreadcrumbRef", { items: TRAIL })],
					...under(
						row("photos"),
						SIZES.map((s) =>
							step(`p-${s}`, "AvatarRef", { src: PHOTO, name: "Ada Lovelace", size: s }),
						),
					),
					...under(
						row("initials"),
						SIZES.map((s) => step(`i-${s}`, "AvatarRef", { name: "Grace Hopper", size: s })),
					),
					...under(
						row("spinners"),
						SIZES.map((s) => step(`s-${s}`, "SpinnerRef", { size: s, label: `Spinner ${s}` })),
					),
					...under(
						row("pills"),
						TONES.map((t) => step(`t-${t}`, "StatusPillRef", { tone: t, label: PILL_LABEL[t] })),
					),
					[...col, step("disc", "SkeletonRef", { shape: "circle", height: 40 })],
					[...col, step("lines", "SkeletonRef", { lines: 3, shape: "text" })],
					[...col, step("block", "SkeletonRef", { shape: "rect", height: 72 })],
				]}
			/>
		);
	},
};

export const InRow: Story = {
	render: () => {
		const row = [step("display-row", "Row", { gap: 3, wrap: true })];
		return (
			<NodeStage
				root="display-row"
				label="row flow: the text skeleton fills, avatar, spinner and pill keep their size"
				chains={under(row, [
					step("who", "AvatarRef", { name: "Ada Lovelace", size: "lg" }),
					step("bar", "SkeletonRef", { lines: 2, shape: "text" }),
					step("busy", "SpinnerRef", { size: "sm", label: "Fetching" }),
					step("state", "StatusPillRef", { tone: "warn", label: "Degraded" }),
				])}
			/>
		);
	},
};

export const InCard: Story = {
	render: () => {
		const card = [
			step("display-card", "Card", { title: "Deploy", subtitle: "rivendell / legolas" }),
		];
		const head = [...card, step("head", "Row", { gap: 3 })];
		return (
			<NodeStage
				root="display-card"
				label="a card that is half loaded, then a write lands on the pill"
				chains={[
					card,
					[...card, step("trail", "BreadcrumbRef", { items: TRAIL.slice(0, 3) })],
					...under(head, [
						step("who", "AvatarRef", { name: "Gor", size: "md" }),
						step("state", "StatusPillRef", { tone: "info", label: "Building" }),
						step("busy", "SpinnerRef", { size: "sm" }),
					]),
					[...card, step("body", "SkeletonRef", { lines: 4, shape: "text" })],
				]}
				frames={[
					{
						op: "write",
						ref: ["display-card", "head", "state"],
						payload: { tone: "ok", label: "Live" },
					},
				]}
			/>
		);
	},
};
