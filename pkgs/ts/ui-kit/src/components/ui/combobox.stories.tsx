import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxGroup,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "./combobox";

const FRUITS = [
	{ value: "apple", label: "Apple" },
	{ value: "banana", label: "Banana" },
	{ value: "cherry", label: "Cherry" },
	{ value: "grape", label: "Grape" },
	{ value: "mango", label: "Mango" },
	{ value: "orange", label: "Orange" },
];

function Sample({ seed = "", open }: { seed?: string; open?: boolean }) {
	const [value, setValue] = useState(seed);
	const selected = FRUITS.find((f) => f.value === value);
	return (
		<Combobox value={value} onValueChange={setValue} defaultOpen={open}>
			<ComboboxTrigger className="w-56">
				<span>{selected ? selected.label : "Pick a fruit"}</span>
			</ComboboxTrigger>
			<ComboboxContent>
				<ComboboxInput placeholder="Search fruit..." />
				<ComboboxList>
					<ComboboxEmpty>No matches.</ComboboxEmpty>
					<ComboboxGroup heading="Fruits">
						{FRUITS.map((f) => (
							<ComboboxItem key={f.value} value={f.value}>
								{f.label}
							</ComboboxItem>
						))}
					</ComboboxGroup>
				</ComboboxList>
			</ComboboxContent>
		</Combobox>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Sample />
			</div>
	),
};

export const Matrix = Default;

// Opened at load with a pick: in touch mode a bottom sheet, the search field
// pinned on top and the options as rows; on desktop the anchored list.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8">
			<Sample seed="cherry" open />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Combobox",
};

export default meta;
