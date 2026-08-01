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

function Sample() {
	const [value, setValue] = useState("");
	const selected = FRUITS.find((f) => f.value === value);
	return (
		<Combobox value={value} onValueChange={setValue}>
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

const meta: Meta = {
	title: "UI/Combobox",
};

export default meta;
