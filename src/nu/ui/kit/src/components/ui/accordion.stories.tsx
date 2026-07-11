import type { Meta, StoryObj } from "@storybook/react-vite";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "./accordion";

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
		a: "Radix for a11y-heavy primitives, cmdk for command surfaces, recharts for charts, react-day-picker for dates.",
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
			</div>
	),
};

const meta: Meta = {
	title: "UI/Accordion",
};

export default meta;
