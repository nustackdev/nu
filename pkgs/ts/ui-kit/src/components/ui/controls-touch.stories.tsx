// The form controls on a phone. Touch changes no control's look or size;
// what it adds is unseen: a 44px tap area around each small control
// (index.css, `nu-tap`). `TapAreas` draws those areas so they can be checked
// by eye, in touch mode only (a phone, a tablet, or the Touch toolbar); on
// desktop the same story shows the plain controls. `Form` is a real form in
// a phone's width: fluid rows wrap, nothing is placed, so nothing stacks.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Bold, Italic, Underline } from "lucide-react";
import { useState } from "react";
import { Button } from "./button";
import { Checkbox } from "./checkbox";
import { CheckboxGroup } from "./checkbox-group";
import { Field, Label } from "./field";
import { FileInput } from "./file-input";
import { Input } from "./input";
import { PasswordInput, SearchInput } from "./input-affix";
import { InputGroup } from "./input-group";
import { NumberInput } from "./number-input";
import { RadioGroup, RadioGroupItem } from "./radio-group";
import { RangeSlider } from "./range-slider";
import { SegmentedControl, SegmentedControlItem } from "./segmented-control";
import { Slider } from "./slider";
import { Switch } from "./switch";
import { TextArea } from "./text-area";
import { Toggle } from "./toggle";

const GENRES = [
	{ value: "drama", label: "Drama" },
	{ value: "comedy", label: "Comedy" },
	{ value: "sci-fi", label: "Sci-fi" },
	{ value: "noir", label: "Noir" },
];

// Story only: outlines every tap area. The areas are `::after` boxes that
// exist in touch mode only, so on desktop this draws nothing.
const SHOW_TAPS = `[data-nu-touch] [data-taps] .nu-tap::after {
	outline: 1px dashed color-mix(in oklab, var(--accent) 70%, transparent);
	background: color-mix(in oklab, var(--accent) 8%, transparent);
	border-radius: 4px;
}`;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
	return (
		<div className="flex flex-col gap-2">
			<div className="font-mono text-xs uppercase tracking-widest text-text-muted">{label}</div>
			<div className="flex flex-wrap items-center gap-4">{children}</div>
		</div>
	);
}

function TapAreasDemo() {
	const [n, setN] = useState<number | null>(4);
	const [search, setSearch] = useState("Arrival");
	return (
		<div data-taps className="flex max-w-xl flex-col gap-6 p-4">
			<style>{SHOW_TAPS}</style>
			<Row label="checkbox, radio, switch">
				<Checkbox aria-label="Seen" defaultChecked />
				<Checkbox aria-label="Owned" size="sm" />
				<RadioGroup defaultValue="a" className="flex gap-3" aria-label="Pick">
					<RadioGroupItem value="a" aria-label="A" />
					<RadioGroupItem value="b" aria-label="B" />
				</RadioGroup>
				<Switch aria-label="Notify" defaultChecked />
				<Switch aria-label="Quiet" size="sm" />
			</Row>
			<Row label="toggle, segmented">
				<div className="flex gap-0.5">
					<Toggle size="sm" aria-label="Bold" defaultPressed>
						<Bold />
					</Toggle>
					<Toggle size="sm" aria-label="Italic">
						<Italic />
					</Toggle>
					<Toggle size="sm" aria-label="Underline">
						<Underline />
					</Toggle>
				</div>
				<SegmentedControl defaultValue="week" size="sm" aria-label="Range">
					<SegmentedControlItem value="day">Day</SegmentedControlItem>
					<SegmentedControlItem value="week">Week</SegmentedControlItem>
					<SegmentedControlItem value="month">Month</SegmentedControlItem>
				</SegmentedControl>
			</Row>
			<Row label="number steppers, affix buttons">
				<div className="w-32">
					<NumberInput aria-label="Copies" value={n} onValueChange={setN} min={0} max={9} />
				</div>
				<div className="w-56">
					<SearchInput
						aria-label="Search"
						value={search}
						onChange={(e) => setSearch(e.currentTarget.value)}
						onClear={() => setSearch("")}
					/>
				</div>
			</Row>
			<Row label="slider thumbs">
				<div className="w-full">
					<Slider defaultValue={[40]} thumbLabels={["Volume"]} />
				</div>
				<div className="w-full">
					<RangeSlider defaultValue={[20, 70]} aria-label="Year" />
				</div>
			</Row>
		</div>
	);
}

export const TapAreas: StoryObj = {
	render: () => <TapAreasDemo />,
};

function FormDemo() {
	const [genres, setGenres] = useState<string[]>(["drama"]);
	const [copies, setCopies] = useState<number | null>(1);
	return (
		<div className="flex max-w-xl flex-col gap-4 p-4">
			<Field label="Title" required>
				<Input placeholder="A film to add" />
			</Field>
			<Field label="Password">
				<PasswordInput aria-label="Password" defaultValue="hunter2" />
			</Field>
			<div className="flex flex-col gap-1">
				<Label id="genres-label">Genres</Label>
				<CheckboxGroup
					aria-labelledby="genres-label"
					orientation="horizontal"
					options={GENRES}
					value={genres}
					onValueChange={setGenres}
				/>
			</div>
			<Field label="Copies" inline>
				<NumberInput value={copies} onValueChange={setCopies} min={0} max={9} className="w-28" />
			</Field>
			<Field label="Notify" inline>
				<Switch defaultChecked />
			</Field>
			<Field label="Rating">
				<Slider defaultValue={[7]} max={10} thumbLabels={["Rating"]} />
			</Field>
			<Field label="Notes" help="Only you see these">
				<TextArea placeholder="What stayed with you" />
			</Field>
			<Field label="Poster">
				<FileInput accept="image/*" maxSize={5_000_000} onFiles={() => {}} />
			</Field>
			<InputGroup>
				<Input aria-label="Tag" placeholder="Add a tag" />
				<Button>Add</Button>
			</InputGroup>
		</div>
	);
}

export const Form: StoryObj = {
	render: () => <FormDemo />,
};

const meta: Meta = {
	title: "UI/ControlsTouch",
};

export default meta;
