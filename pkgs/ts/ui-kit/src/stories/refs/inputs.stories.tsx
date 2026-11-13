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

export const Choices: Story = {
	render: () => {
		const grid = step("inputs-choices", "Grid", {
			max_columns: 2,
			min_cell_width: 260,
			gap: 6,
			align: "start",
		});
		return (
			<NodeStage
				root="inputs-choices"
				label="one pick from a row, several from a list or a dropdown, free text with suggestions"
				chains={[
					[
						grid,
						step("range", "SegmentedControlRef", {
							label: "Range",
							options: ["Day", "Week", "Month"],
							value: "Week",
						}),
					],
					[
						grid,
						step("genres", "CheckboxGroupRef", {
							label: "Genres",
							options: ["drama", "comedy", "sci-fi", "documentary"],
							value: ["drama", "sci-fi"],
							orientation: "horizontal",
						}),
					],
					[
						grid,
						step("packages", "MultiSelectRef", {
							label: "Packages",
							options: PACKAGES,
							value: ["nu", "nustd", "nudle"],
							placeholder: "Pick packages",
						}),
					],
					[
						grid,
						step("package", "AutocompleteRef", {
							label: "Package, or anything",
							options: PACKAGES,
							value: "",
							placeholder: "Type nu...",
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
	["DateRangePickerRef", { value: { start: "2016-11-11", end: "2016-11-13" } }],
	["DateTimePickerRef", { value: "2016-11-11T19:30" }],
	["TimePickerRef", { value: "19:30" }],
	["CheckboxRef", { value: true }],
	["SwitchRef", { value: true }],
	["RadioGroupRef", { options: ["drama", "comedy"], value: "drama" }],
	["SliderRef", { value: 40 }],
	["RangeSliderRef", { value: [20, 60] }],
	["ColorPickerRef", { value: "#4269d0" }],
	["SegmentedControlRef", { options: ["Day", "Week", "Month"], value: "Week" }],
	["CheckboxGroupRef", { options: ["drama", "comedy", "sci-fi"], value: ["drama"] }],
	["MultiSelectRef", { options: PACKAGES, value: ["nu", "nustd"] }],
	["AutocompleteRef", { options: PACKAGES, value: "nudle", placeholder: "Package" }],
	["InlineEditRef", { value: "Arrival", placeholder: "Untitled" }],
];

export const RangeAndColor: Story = {
	render: () => {
		const col = step("inputs-range-color", "Column", { gap: 6 });
		return (
			<NodeStage
				root="inputs-range-color"
				label="a release or an arrow key sends one change; Enter in the hex field submits"
				chains={[
					[
						col,
						step("salary", "RangeSliderRef", {
							label: "Salary",
							value: [40, 120],
							max: 200,
							format: "{}k",
						}),
					],
					[
						col,
						step("share", "RangeSliderRef", {
							label: "Share",
							min: 0,
							max: 1,
							step: 0.05,
							value: [0.25, 0.75],
							marks: [0, { value: 0.5, label: "half" }, 1],
							thumb_labels: ["From", "To"],
						}),
					],
					[
						col,
						step("accent", "ColorPickerRef", {
							label: "Accent",
							value: "#8946db",
							swatches: "palette",
						}),
					],
					[
						col,
						step("ink", "ColorPickerRef", {
							label: "Ink",
							value: "#111111",
							swatches: ["#111111", "#555555", "#999999", "#dddddd"],
						}),
					],
				]}
			/>
		);
	},
};

export const Dates: Story = {
	render: () => {
		const grid = step("inputs-dates", "Grid", {
			max_columns: 2,
			min_cell_width: 280,
			gap: 6,
			align: "start",
		});
		return (
			<NodeStage
				root="inputs-dates"
				label="a time with seconds, a date and time with bounds, a range, all clearable; Enter submits"
				chains={[
					[grid, step("at", "TimePickerRef", { label: "Alarm", value: "06:45:30", step: 1 })],
					[
						grid,
						step("starts", "DateTimePickerRef", {
							label: "Screening",
							value: "2016-11-11T19:30",
							min: "2016-11-01T10:00",
							max: "2016-11-30T23:00",
						}),
					],
					[
						grid,
						step("stay", "DateRangePickerRef", {
							label: "Festival",
							value: { start: "2016-11-11", end: "2016-11-13" },
						}),
					],
					[grid, step("empty", "DateTimePickerRef", { label: "Not set", value: "" })],
				]}
			/>
		);
	},
};

export const TypesAndGroups: Story = {
	render: () => {
		const col = step("inputs-kinds", "Column", { gap: 6, max_width: "form" });
		const say = step("say", "InputGroup", {});
		const find = step("find", "InputGroup", {});
		const job = step("job", "InputGroup", {});
		return (
			<NodeStage
				root="inputs-kinds"
				label="search with clear, password with reveal, email / url / tel, inline edit, and inputs grouped with their buttons"
				chains={[
					[
						col,
						step("search", "InputRef", {
							type: "search",
							value: "arrival",
							placeholder: "Search films",
						}),
					],
					[
						col,
						step("password", "InputRef", {
							type: "password",
							label: "Password",
							value: "correct horse",
						}),
					],
					[
						col,
						step("email", "InputRef", {
							type: "email",
							label: "Email",
							placeholder: "you@example.com",
						}),
					],
					[col, step("url", "InputRef", { type: "url", label: "Site", placeholder: "https://" })],
					[
						col,
						step("tel", "InputRef", { type: "tel", label: "Phone", placeholder: "+1 555 0100" }),
					],
					[
						col,
						step("title", "InlineEditRef", {
							label: "Title",
							value: "Field notes",
							placeholder: "Untitled",
						}),
					],
					[
						col,
						step("key", "InlineEditRef", {
							label: "Key",
							value: "notes",
							error: "That key is taken",
						}),
					],
					[
						col,
						step("empty", "InlineEditRef", { value: "", placeholder: "Add a name", size: "lg" }),
					],
					[
						col,
						find,
						step("q", "InputRef", { type: "search", value: "", placeholder: "Search the base" }),
					],
					[col, find, step("go", "ButtonRef", { label: "Search", variant: "secondary" })],
					[col, job, step("name", "InputRef", { label: "New job", placeholder: "Job name" })],
					[col, job, step("create", "ButtonRef", { label: "Create job" })],
					[col, say, step("text", "InputRef", { placeholder: "Say something" })],
					[col, say, step("send", "ButtonRef", { label: "Say", icon: "send" })],
					[
						col,
						say,
						step("stop", "ButtonRef", { label: "Stop", icon: "square", variant: "secondary" }),
					],
				]}
			/>
		);
	},
};

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
