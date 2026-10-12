// Refs/Inputs: the input leaves as a program draws them. A toolbar Row of
// icon buttons and toggles (one height, so they line up), buttons with an
// icon before the label in every variant, and a searchable select next to a
// plain one over the same options.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Inputs",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

const ghost = (segment: string, icon: string, tooltip: string) =>
	step(segment, "ButtonRef", { label: "", variant: "ghost", icon, tooltip });

export const Toolbar: Story = {
	render: () => {
		const bar = step("inputs-toolbar", "Row", { gap: 1, align: "center" });
		return (
			<NodeStage
				root="inputs-toolbar"
				label="icon buttons with tooltips, toggles, a divider, a labelled button"
				chains={[
					[bar, ghost("back", "arrow-left", "Back")],
					[bar, ghost("reload", "refresh-cw", "Reload")],
					[bar, ghost("search", "search", "Search")],
					[bar, step("sep", "DividerRef")],
					[bar, step("bold", "ToggleRef", { icon: "bold", pressed: true })],
					[bar, step("wrap", "ToggleRef", { icon: "wrap-text", label: "Wrap" })],
					[bar, step("sep2", "DividerRef")],
					[bar, ghost("more", "more-horizontal", "More")],
					[bar, step("run", "ButtonRef", { label: "Run", icon: "play" })],
				]}
			/>
		);
	},
};

export const Variants: Story = {
	render: () => {
		const row = step("inputs-variants", "Row", { gap: 2, align: "center", wrap: true });
		return (
			<NodeStage
				root="inputs-variants"
				label="icon before label, one per variant, then icon-only in each"
				chains={[
					[row, step("primary", "ButtonRef", { label: "Add", icon: "plus" })],
					[
						row,
						step("secondary", "ButtonRef", { label: "Copy", icon: "copy", variant: "secondary" }),
					],
					[row, step("ghost", "ButtonRef", { label: "Filter", icon: "filter", variant: "ghost" })],
					[
						row,
						step("soft", "ButtonRef", { label: "Settings", icon: "settings", variant: "soft" }),
					],
					[
						row,
						step("danger", "ButtonRef", { label: "Delete", icon: "trash-2", variant: "danger" }),
					],
					[row, step("p-icon", "ButtonRef", { icon: "plus", tooltip: "Add" })],
					[
						row,
						step("s-icon", "ButtonRef", { icon: "copy", tooltip: "Copy", variant: "secondary" }),
					],
					[
						row,
						step("g-icon", "ButtonRef", { icon: "filter", tooltip: "Filter", variant: "ghost" }),
					],
					[
						row,
						step("o-icon", "ButtonRef", { icon: "settings", tooltip: "Settings", variant: "soft" }),
					],
					[
						row,
						step("d-icon", "ButtonRef", { icon: "trash-2", tooltip: "Delete", variant: "danger" }),
					],
				]}
			/>
		);
	},
};

const PACKAGES = [
	"nu",
	"nustd",
	"nucli",
	"nulog",
	"nuspace",
	"nuagent",
	"virtuals",
	"invisibles",
	"rdbpy",
	"kh57",
].map((value) => ({ value, label: value }));

export const Selects: Story = {
	render: () => {
		const row = step("inputs-selects", "Row", { gap: 4, align: "end" });
		return (
			<NodeStage
				root="inputs-selects"
				label="plain and searchable over the same options"
				chains={[
					[
						row,
						step("plain", "SelectRef", { label: "Package", options: PACKAGES, selected: "nustd" }),
					],
					[
						row,
						step("search", "SelectRef", {
							label: "Package, searchable",
							options: PACKAGES,
							selected: "",
							placeholder: "Pick a package",
							searchable: true,
						}),
					],
				]}
			/>
		);
	},
};
