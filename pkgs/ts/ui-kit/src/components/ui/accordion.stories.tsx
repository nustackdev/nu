import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./accordion";
import { Badge } from "./badge";
import { Button } from "./button";

const ITEMS = [
	{
		value: "one",
		q: "What is Nu?",
		a: "A programming model for building UIs as pure data structures. The kit supplies the primitives; Nu supplies the composition.",
	},
	{
		value: "two",
		q: "Why an IDE flavor?",
		a: "The kit exists to build tools, data viewers, control panels. Density, keyboard-first behavior, and a calm canvas beat marketing gloss.",
	},
	{
		value: "three",
		q: "Which libraries under the hood?",
		a: "Radix for a11y-heavy primitives, cmdk for command surfaces, ECharts for charts, react-day-picker for dates.",
	},
];

function Items() {
	return (
		<>
			{ITEMS.map((it) => (
				<AccordionItem key={it.value} value={it.value}>
					<AccordionTrigger>{it.q}</AccordionTrigger>
					<AccordionContent>{it.a}</AccordionContent>
				</AccordionItem>
			))}
		</>
	);
}

function SampleSingle() {
	return (
		<Accordion type="single" collapsible defaultValue="one">
			<Items />
		</Accordion>
	);
}

function SampleMultiple() {
	return (
		<Accordion type="multiple" defaultValue={["one", "three"]}>
			<Items />
		</Accordion>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-lg">
			<SampleSingle />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8 max-w-lg">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					type=single (collapsible)
				</div>
				<SampleSingle />
			</div>
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					type=multiple
				</div>
				<SampleMultiple />
			</div>
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					header row
				</div>
				<SampleHeader />
			</div>
		</div>
	),
};

// A header row in place of the plain label: a name that truncates, a badge
// and a button. A click on the name or the empty space toggles the section;
// the button does its own thing.
function SampleHeader() {
	const [runs, setRuns] = useState(0);
	return (
		<Accordion type="multiple" variant="boxed" defaultValue={["build"]}>
			<AccordionItem value="build">
				<AccordionTrigger
					header={
						<div className="flex min-w-0 items-center gap-2">
							<span className="min-w-0 flex-1 truncate text-sm font-medium text-text-primary">
								Build web-03 from main with a long name that truncates
							</span>
							<Badge variant="ok">passed</Badge>
							<Button size="sm" variant="ghost" onClick={() => setRuns((n) => n + 1)}>
								Rerun{runs ? ` (${runs})` : ""}
							</Button>
						</div>
					}
				/>
				<AccordionContent>Built in 42s.</AccordionContent>
			</AccordionItem>
			<AccordionItem value="deploy">
				<AccordionTrigger>Deploy</AccordionTrigger>
				<AccordionContent>Not deployed yet.</AccordionContent>
			</AccordionItem>
		</Accordion>
	);
}

export const Header: StoryObj = {
	render: () => (
		<div className="p-8 max-w-lg">
			<SampleHeader />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Accordion",
};

export default meta;
