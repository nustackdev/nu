// Refs/Inputs: the input leaves as a program draws them. A toolbar Row of
// icon buttons and toggles (one height, so they line up), buttons with an
// icon before the label in every variant, a searchable select next to a
// plain one over the same options, a sketch board (a digit pad beside a board
// a program drew on), the common states (disabled, readonly, required,
// invalid through a Field) on every input, and a Form that submits on Enter
// or its submit button and not on Cancel, and one that checks its fields
// before it sends, with a disabled Fieldset in it. The send key on each
// multi-line input (shift+Enter by default, or Enter), with what it last
// sent under it, and a CodeRef in diff mode: a change with highlighting, a
// new file, and a long file whose unchanged runs fold. The moving inputs,
// each with the last `input` event it sent under it.

import type { TreeFrame } from "@nustackdev/ui-core";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";
import { tree, unbatch } from "../../tree";
import { type NodeSeed, NodeStage, sinkParameters, step } from "./harness";

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
	["IconPickerRef", { value: "lucide:rocket" }],
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
				label="a drag sends an input per tick, a release or an arrow key one change; Enter in the hex field submits; an icon pick sends one change"
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
					[col, step("mark", "IconPickerRef", { label: "Icon", value: "emoji:🌱" })],
					[
						col,
						step("glyph", "IconPickerRef", {
							label: "Glyph",
							value: "",
							kinds: ["lucide"],
							placeholder: "Pick a glyph",
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
							placeholder: "shift+Enter submits",
						}),
					],
					[form, actions, step("cancel", "ButtonRef", { label: "Cancel", variant: "secondary" })],
					[form, actions, step("save", "ButtonRef", { label: "Log it", submit: true })],
				]}
			/>
		);
	},
};

export const FormChecks: Story = {
	render: () => {
		const form = step("inputs-checks", "Form", { title: "Sign up" });
		const plan = step("plan", "Fieldset", { legend: "Plan (locked)", disabled: true });
		return (
			<NodeStage
				root="inputs-checks"
				label="Sign up with Name empty, a bad email or an age under 18: the Field shows why and the first one takes focus. The locked Fieldset disables what is in it"
				chains={[
					[
						form,
						step("name", "Field", { label: "Name", required: true }),
						step("control", "InputRef", { value: "" }),
					],
					[form, step("email", "InputRef", { label: "Email", type: "email", value: "" })],
					[
						form,
						step("age", "Field", { label: "Age", help: "18 or over" }),
						step("control", "NumberInputRef", { value: null, min: 18 }),
					],
					[
						form,
						plan,
						step("tier", "SelectRef", { label: "Tier", value: null, options: ["Free", "Pro"] }),
					],
					[form, plan, step("upgrade", "ButtonRef", { label: "Upgrade", variant: "secondary" })],
					[form, step("go", "ButtonRef", { label: "Sign up", submit: true })],
				]}
			/>
		);
	},
};

const DIFF_BEFORE = `def total(rows):
    out = 0
    for row in rows:
        out += row.price
    return out


def average(rows):
    return total(rows) / len(rows)


def cheapest(rows):
    return min(rows, key=lambda r: r.price)


def dearest(rows):
    return max(rows, key=lambda r: r.price)
`;

const DIFF_AFTER = DIFF_BEFORE.replace(
	"    out = 0\n    for row in rows:\n        out += row.price\n    return out\n",
	"    return sum(row.price for row in rows)\n",
).replace(
	"    return total(rows) / len(rows)\n",
	"    return total(rows) / len(rows) if rows else 0.0\n",
);

// A long module where two edits sit far apart, so the runs between, before
// and after them fold.
const LONG_BEFORE = Array.from(
	{ length: 24 },
	(_, i) => `def step_${i}(x):\n    """Step ${i} of the pipeline."""\n    return x + ${i}\n\n`,
).join("");

const LONG_AFTER = LONG_BEFORE.replace("    return x + 3\n", "    return (x + 3) * 2\n").replace(
	'    """Step 19 of the pipeline."""\n',
	'    """Step 19 of the pipeline, now logged."""\n    log.debug("step 19", x)\n',
);

const NEW_FILE = `#!/bin/sh
set -eu
uv sync
uv run pytest -q
`;

export const CodeDiff: Story = {
	render: () => {
		const col = step("inputs-diff", "Column", { gap: 6 });
		const caption = (seg: string, value: string) =>
			step(seg, "TextRef", { value, size: "xs", tone: "muted", mono: true });
		return (
			<NodeStage
				root="inputs-diff"
				label="CodeRef with an original: a read-only unified diff, unchanged runs folded"
				chains={[
					[col, caption("c-lang", "python, a function rewritten and a line changed")],
					[
						col,
						step("diff", "CodeRef", {
							value: DIFF_AFTER,
							original: DIFF_BEFORE,
							language: "python",
							line_numbers: true,
						}),
					],
					[col, caption("c-new", 'a new file: original=""')],
					[
						col,
						step("new", "CodeRef", {
							value: NEW_FILE,
							original: "",
							language: "shell",
							line_numbers: true,
						}),
					],
					[col, caption("c-long", "~100 lines, two edits far apart, the runs around them folded")],
					[
						col,
						step("long", "CodeRef", {
							value: LONG_AFTER,
							original: LONG_BEFORE,
							language: "python",
							line_numbers: true,
						}),
					],
				]}
			/>
		);
	},
};

// Stands in for the program while a story is mounted: every `event` under
// `root` lands as the text of the `sent` leaf in the grid cell it came from.
// A batch frame is opened into its notifies first.
function useEcho(root: string, event: string, prefix: string): void {
	useEffect(() => {
		const store = tree.getState();
		store.setSender((sent: TreeFrame) => {
			for (const frame of unbatch([sent])) {
				const payload = frame.payload as { event?: string; value?: unknown } | null;
				if (frame.ref?.[0] !== root || payload?.event !== event) continue;
				// root (the grid) / cell / ...: the echo sits in the cell.
				const { event: _event, ...fields } = payload;
				const shown = "draft" in fields ? fields : payload.value;
				const at = [...frame.ref.slice(0, 2), "sent"];
				store.setProps(at, { value: `${prefix}: ${JSON.stringify(shown)}` });
			}
		});
		return () => store.setSender(null);
	}, [root, event, prefix]);
}

function EchoStage(s: NodeSeed & { label?: string; event?: string; prefix?: string }) {
	const { event = "submit", prefix = "last sent", ...stage } = s;
	useEcho(stage.root, event, prefix);
	return <NodeStage {...stage} />;
}

const MOVING: [string, Record<string, unknown>][] = [
	["InputRef", { value: "", placeholder: "Type" }],
	["NumberInputRef", { value: 3 }],
	["TagInputRef", { value: ["nu"], placeholder: "Add a tag" }],
	["SliderRef", { value: 40 }],
	["RangeSliderRef", { value: [20, 60] }],
	["ColorPickerRef", { value: "#8946db" }],
];

export const Moving: Story = {
	render: () => {
		const root = "inputs-moving";
		const grid = step(root, "Grid", {
			max_columns: 3,
			min_cell_width: 200,
			gap: 4,
			align: "start",
		});
		const chains = MOVING.flatMap(([kind, props]) => {
			const cell = step(kind, "Column", { gap: 2 });
			return [
				[grid, cell, step("field", kind, { label: kind, ...props })],
				[
					grid,
					cell,
					step("sent", "TextRef", {
						value: "input: nothing yet",
						size: "xs",
						tone: "secondary",
						mono: true,
					}),
				],
			];
		});
		return (
			<EchoStage
				root={root}
				event="input"
				prefix="input"
				label="each keystroke or drag tick sends an input with the value; the last one heard shows under each"
				chains={chains}
			/>
		);
	},
};

const SEND_KEYS = [
	["shift+enter", "shift+Enter sends"],
	["enter", "Enter sends"],
] as const;

export const SendKey: Story = {
	render: () => {
		const root = "inputs-send-key";
		const grid = step(root, "Grid", {
			max_columns: 3,
			min_cell_width: 200,
			gap: 4,
			align: "start",
		});
		const chains = SEND_KEYS.flatMap(([key, hint]) => {
			const on = key === "enter" ? { submit_on: "enter" } : {};
			const cell = (kind: string) => step(`${kind}-${key}`, "Column", { gap: 2 });
			const caption = (kind: string) =>
				step("caption", "TextRef", {
					value: `${kind}, submit_on=${key === "enter" ? '"enter"' : "default"}`,
					size: "xs",
					tone: "muted",
					mono: true,
				});
			const sent = step("sent", "TextRef", {
				value: "last sent: nothing yet",
				size: "xs",
				tone: "secondary",
				mono: true,
			});
			const ta = cell("textarea");
			const code = cell("code");
			const md = cell("markdown");
			return [
				[grid, ta, caption("TextAreaRef")],
				[grid, ta, step("field", "TextAreaRef", { value: "", rows: 3, placeholder: hint, ...on })],
				[grid, ta, sent],
				[grid, code, caption("CodeRef")],
				[
					grid,
					code,
					step("field", "CodeRef", {
						value: `# ${hint}\nprint("hi")\n`,
						language: "python",
						readonly: false,
						min_height: 96,
						...on,
					}),
				],
				[grid, code, sent],
				[grid, md, caption("MarkdownRef")],
				[
					grid,
					md,
					step("box", "Card", { variant: "outline", size: "sm" }),
					step("field", "MarkdownRef", { value: "", readonly: false, placeholder: hint, ...on }),
				],
				[grid, md, sent],
			];
		});
		return (
			<EchoStage
				root={root}
				label="each input's send key, default (shift+Enter) on the first row and Enter on the second; what it sent shows under it"
				chains={chains}
			/>
		);
	},
};
