// Refs/Quote: a header line over a body, set apart as quoted, as a program
// draws it. A citation takes its source as a header Row, a trace of work
// takes a Row of icon, label and a time pushed to the end, a note takes the
// string title, and a narrow one shows the header truncating inside.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Quote",
	parameters: { layout: "fullscreen" },
};

export default meta;

type Story = StoryObj;

export const Quote: Story = {
	parameters: sinkParameters,
	render: () => {
		const col = step("quote-col", "Column", { gap: 6, max_width: 480 });

		const cite = step("cite", "Quote");
		const citeHead = step("header", "Row", { gap: 2 });

		const trace = step("trace", "Quote");
		const traceHead = step("header", "Row", { gap: 2, grow: { label: 1 } });

		const note = step("note", "Quote", { title: "Note" });

		const narrow = step("narrow", "Quote", { max_width: 220 });
		const narrowHead = step("header", "Row", { gap: 2, grow: { label: 1 } });

		return (
			<NodeStage
				root="quote-col"
				label="citation, trace, titled note, truncating header"
				chains={[
					[col, cite, citeHead, step("icon", "IconRef", { name: "book-open", size: "sm" })],
					[
						col,
						cite,
						citeHead,
						step("src", "TextRef", {
							value: "RFC 9110, section 9.2.2",
							size: "sm",
							weight: "medium",
						}),
					],
					[
						col,
						cite,
						step("body", "TextRef", {
							value:
								"A request method is idempotent if the effect of several identical requests is the same as the effect of one.",
						}),
					],
					[col, trace, traceHead, step("icon", "IconRef", { name: "sparkles", size: "sm" })],
					[
						col,
						trace,
						traceHead,
						step("label", "TextRef", { value: "Working", size: "sm", weight: "medium" }),
					],
					[
						col,
						trace,
						traceHead,
						step("when", "TextRef", { value: "12s", size: "sm", tone: "muted" }),
					],
					[
						col,
						trace,
						step("a", "TextRef", { value: "Read the deploy config and the last three runs." }),
					],
					[
						col,
						trace,
						step("b", "TextRef", { value: "The cache key changed, so the build starts cold." }),
					],
					[col, note, step("body", "TextRef", { value: "Changes apply on the next deploy." })],
					[col, narrow, narrowHead, step("icon", "IconRef", { name: "sparkles", size: "sm" })],
					[
						col,
						narrow,
						narrowHead,
						step("label", "TextRef", {
							value: "A header line far too long for its box",
							size: "sm",
							weight: "medium",
							lines: 1,
						}),
					],
					[
						col,
						narrow,
						narrowHead,
						step("when", "TextRef", { value: "3m", size: "sm", tone: "muted" }),
					],
					[col, narrow, step("body", "TextRef", { value: "The body wraps as usual." })],
				]}
			/>
		);
	},
};
