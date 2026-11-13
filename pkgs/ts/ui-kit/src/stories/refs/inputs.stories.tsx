// Refs/Inputs: the input leaves as a program draws them. A toolbar Row of
// icon buttons and toggles (one height, so they line up), buttons with an
// icon before the label in every variant, a searchable select next to a
// plain one over the same options, a sketch board (a digit pad beside a board
// a program drew on), the common states (disabled, readonly, required,
// invalid through a Field) on every input, and a Form that submits on Enter
// or its submit button and not on Cancel.

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
					[bar, step("bold", "ToggleRef", { icon: "bold", value: true })],
					[bar, step("wrap", "ToggleRef", { icon: "text-wrap", label: "Wrap" })],
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
					[row, step("ghost", "ButtonRef", { label: "Filter", icon: "funnel", variant: "ghost" })],
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
						step("g-icon", "ButtonRef", { icon: "funnel", tooltip: "Filter", variant: "ghost" }),
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
	"nudle",
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
						step("plain", "SelectRef", { label: "Package", options: PACKAGES, value: "nustd" }),
					],
					[
						row,
						step("search", "SelectRef", {
							label: "Package, searchable",
							options: PACKAGES,
							value: "",
							placeholder: "Pick a package",
							searchable: true,
						}),
					],
				]}
			/>
		);
	},
};

export const Sketch: Story = {
	render: () => {
		const row = step("inputs-sketch", "Row", { gap: 4, align: "start", wrap: true });
		return (
			<NodeStage
				root="inputs-sketch"
				label="a pen-only digit pad, and a board a program drew on"
				chains={[
					[
						row,
						step("digit", "SketchRef", {
							label: "Draw a digit",
							width: 200,
							tools: ["pen"],
							controls: ["clear"],
							defaults: { size: 0.07 },
							value: [],
						}),
					],
					[
						row,
						step("drawn", "SketchRef", {
							label: "Written by the server",
							width: 320,
							height: 220,
							value: [
								{
									type: "rect",
									x: 0.08,
									y: 0.3,
									w: 0.3,
									h: 0.3,
									stroke: "blue",
									fill: "blue-soft",
								},
								{
									type: "arrow",
									points: [
										[0.42, 0.45],
										[0.58, 0.45],
									],
								},
								{
									type: "ellipse",
									x: 0.62,
									y: 0.28,
									w: 0.3,
									h: 0.34,
									stroke: "violet",
									fill: "violet-soft",
								},
							],
						}),
					],
				]}
			/>
		);
	},
};

const states = (kind: string, props: Record<string, unknown>) => {
	const col = step(`inputs-states-${kind}`, "Column", { gap: 3 });
	return [
		[col, step("plain", kind, { ...props, label: "Plain" })],
		[col, step("disabled", kind, { ...props, label: "Disabled", disabled: true })],
		[col, step("readonly", kind, { ...props, label: "Readonly", readonly: true })],
		[col, step("required", kind, { ...props, label: "Required", required: true })],
		[
			col,
			step("invalid", "Field", {
				label: "Invalid, through a Field",
				help: "Help stays when the error shows",
				error: "That will not do",
				required: true,
			}),
			step("control", kind, props),
		],
	];
};

const STATE_KINDS: [string, Record<string, unknown>][] = [
	["InputRef", { value: "Arrival", placeholder: "Title" }],
	["NumberInputRef", { value: 2016 }],
	["TextAreaRef", { value: "Quiet, patient, strange.", rows: 2 }],
	["SelectRef", { options: PACKAGES, value: "nustd" }],
	["TagInputRef", { value: ["sci-fi", "2016"] }],
	["DatePickerRef", { value: "2016-11-11" }],
	["CheckboxRef", { value: true }],
	["SwitchRef", { value: true }],
	["RadioGroupRef", { options: ["drama", "comedy"], value: "drama" }],
	["SliderRef", { value: 40 }],
];

export const States: Story = {
	render: () => {
		const grid = step("inputs-states", "Grid", {
			max_columns: 3,
			min_cell_width: 240,
			gap: 6,
			align: "start",
		});
		return (
			<NodeStage
				root="inputs-states"
				label="plain, disabled, readonly, required and invalid (a Field's error) on each input"
				chains={STATE_KINDS.flatMap(([kind, props]) =>
					states(kind, props).map((chain) => [grid, ...chain]),
				)}
			/>
		);
	},
};

export const FormSubmit: Story = {
	render: () => {
		const form = step("inputs-form", "Form", { title: "Log a movie", clear_on_submit: true });
		const actions = step("actions", "Row", { gap: 2, justify: "end" });
		return (
			<NodeStage
				root="inputs-form"
				label="Enter in Title, or Log it, submits once with every value; Cancel does not submit"
				chains={[
					[
						form,
						step("title", "Field", { label: "Title", help: "As released", required: true }),
						step("control", "InputRef", { value: "", placeholder: "e.g. Arrival" }),
					],
					[form, step("year", "NumberInputRef", { label: "Year", value: 2020 })],
					[
						form,
						step("notes", "TextAreaRef", {
							label: "Notes",
							value: "",
							rows: 2,
							placeholder: "cmd+Enter submits",
						}),
					],
					[form, actions, step("cancel", "ButtonRef", { label: "Cancel", variant: "secondary" })],
					[form, actions, step("save", "ButtonRef", { label: "Log it", submit: true })],
				]}
			/>
		);
	},
};
