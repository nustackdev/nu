// Kitchen sink: every control in every state, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Bold, Italic, Plus, Search, Star, Trash2, Underline } from "lucide-react";
import { useState } from "react";
import { Button } from "../../components/ui/button";
import { Checkbox } from "../../components/ui/checkbox";
import { Combobox, ComboboxTrigger } from "../../components/ui/combobox";
import { DatePicker } from "../../components/ui/date-picker";
import { IconButton } from "../../components/ui/icon-button";
import { InlineEdit } from "../../components/ui/inline-edit";
import { Input } from "../../components/ui/input";
import { Kbd } from "../../components/ui/kbd";
import { NumberInput } from "../../components/ui/number-input";
import { RadioGroup, RadioGroupItem } from "../../components/ui/radio-group";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "../../components/ui/select";
import { Shortcut } from "../../components/ui/shortcut";
import { Slider } from "../../components/ui/slider";
import { Switch } from "../../components/ui/switch";
import { TagInput } from "../../components/ui/tag-input";
import { Text } from "../../components/ui/text";
import { TextArea } from "../../components/ui/text-area";
import { Toggle } from "../../components/ui/toggle";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const BUTTON_VARIANTS = [
	"default",
	"secondary",
	"outline",
	"ghost",
	"soft",
	"destructive",
	"link",
] as const;
const SIZES = ["xs", "sm", "md", "lg"] as const;
const FIELD_VARIANTS = ["default", "ghost", "filled"] as const;

function Buttons() {
	return (
		<Block title="Button">
			{BUTTON_VARIANTS.map((variant) => (
				<Row key={variant} label={variant}>
					{SIZES.map((size) => (
						<Button key={size} variant={variant} size={size}>
							{size}
						</Button>
					))}
					<Button variant={variant}>
						<Plus />
						With icon
					</Button>
					<Button variant={variant} disabled>
						Disabled
					</Button>
				</Row>
			))}
			<Row label="destructive icon">
				<Button variant="destructive">
					<Trash2 />
					Delete plane
				</Button>
				<Button variant="outline">
					Next
					<Star />
				</Button>
			</Row>
		</Block>
	);
}

function IconButtons() {
	return (
		<Block title="IconButton">
			{BUTTON_VARIANTS.map((variant) => (
				<Row key={variant} label={variant}>
					{SIZES.map((size) => (
						<IconButton key={size} variant={variant} size={size} aria-label={`${variant} ${size}`}>
							<Search />
						</IconButton>
					))}
					<IconButton variant={variant} disabled aria-label="Disabled">
						<Trash2 />
					</IconButton>
				</Row>
			))}
		</Block>
	);
}

function Fields() {
	const [tags, setTags] = useState(["nu", "kit", "dark"]);
	return (
		<Block title="Fields">
			<Row label="Input">
				<Input className="w-48" defaultValue="Plane one" />
				<Input className="w-48" placeholder="Placeholder" />
				<Input className="w-48" placeholder="Disabled" disabled />
				<Input className="w-48" defaultValue="Bad value" invalid />
			</Row>
			<Row label="Input sizes">
				<Input className="w-36" size="sm" placeholder="sm" />
				<Input className="w-36" size="md" placeholder="md" />
				<Input className="w-36" size="lg" placeholder="lg" />
			</Row>
			<Row label="TextArea">
				<TextArea className="w-60" placeholder="Notes..." />
				<TextArea className="w-60" defaultValue="Invalid text" invalid />
				<TextArea className="w-60" placeholder="Disabled" disabled />
			</Row>
			<Row label="NumberInput">
				{FIELD_VARIANTS.map((variant) => (
					<NumberInput key={variant} className="w-32" variant={variant} value={42} />
				))}
				<NumberInput className="w-32" value={7} invalid />
				<NumberInput className="w-32" value={3} disabled />
				<NumberInput className="w-24" value={12} steppers={false} />
			</Row>
			<Row label="Select">
				{FIELD_VARIANTS.map((variant) => (
					<Select key={variant} defaultValue="py">
						<SelectTrigger variant={variant} className="w-40">
							<SelectValue />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="py">Python ({variant})</SelectItem>
							<SelectItem value="ts">TypeScript</SelectItem>
						</SelectContent>
					</Select>
				))}
				<Select>
					<SelectTrigger className="w-40">
						<SelectValue placeholder="Placeholder" />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="a">A</SelectItem>
					</SelectContent>
				</Select>
				<Select defaultValue="a">
					<SelectTrigger className="w-40" invalid>
						<SelectValue />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="a">Invalid</SelectItem>
					</SelectContent>
				</Select>
				<Select defaultValue="a" disabled>
					<SelectTrigger className="w-40">
						<SelectValue />
					</SelectTrigger>
					<SelectContent>
						<SelectItem value="a">Disabled</SelectItem>
					</SelectContent>
				</Select>
			</Row>
			<Row label="Combobox">
				{FIELD_VARIANTS.map((variant) => (
					<Combobox key={variant} value="nulog">
						<ComboboxTrigger variant={variant} className="w-40">
							nulog ({variant})
						</ComboboxTrigger>
					</Combobox>
				))}
			</Row>
			<Row label="DatePicker">
				<DatePicker className="w-44" defaultValue={new Date(2026, 9, 14)} />
				<DatePicker className="w-44" placeholder="Pick a date" />
				<DatePicker className="w-44" variant="filled" invalid />
				<DatePicker className="w-44" disabled />
			</Row>
			<Row label="TagInput">
				<TagInput className="w-72" value={tags} onValueChange={setTags} placeholder="Add tag" />
				<TagInput className="w-56" value={[]} onValueChange={() => {}} placeholder="Empty" />
				<TagInput className="w-56" variant="filled" value={["filled"]} onValueChange={() => {}} />
				<TagInput className="w-56" value={["bad"]} onValueChange={() => {}} invalid />
				<TagInput className="w-56" value={["off"]} onValueChange={() => {}} disabled />
			</Row>
			<Row label="InlineEdit">
				<div className="flex w-56 items-center rounded-md bg-bg-hover px-1 py-1">
					<InlineEdit initial="notes.md" label="Rename notes.md" onCommit={() => {}} onCancel={() => {}} />
				</div>
			</Row>
		</Block>
	);
}

function Choices() {
	return (
		<Block title="Choices">
			<Row label="Checkbox">
				<Checkbox aria-label="Unchecked" />
				<Checkbox aria-label="Checked" defaultChecked />
				<Checkbox aria-label="Indeterminate" checked="indeterminate" />
				<Checkbox aria-label="Disabled" disabled />
				<Checkbox aria-label="Disabled checked" disabled defaultChecked />
				<Checkbox aria-label="Invalid" invalid />
				<Checkbox aria-label="Small" size="sm" defaultChecked />
				<Checkbox aria-label="Large" size="lg" defaultChecked />
			</Row>
			<Row label="RadioGroup">
				<RadioGroup defaultValue="b" className="flex gap-4">
					{["a", "b", "c"].map((v) => (
						<label key={v} className="flex items-center gap-2">
							<RadioGroupItem value={v} disabled={v === "c"} />
							<Text as="span" size="sm">
								Option {v.toUpperCase()}
								{v === "c" ? " (disabled)" : ""}
							</Text>
						</label>
					))}
				</RadioGroup>
			</Row>
			<Row label="Switch">
				<Switch aria-label="Off" />
				<Switch aria-label="On" defaultChecked />
				<Switch aria-label="Disabled" disabled />
				<Switch aria-label="Disabled on" disabled defaultChecked />
				<Switch aria-label="Small" size="sm" defaultChecked />
				<Switch aria-label="Large" size="lg" defaultChecked />
			</Row>
			<Row label="Slider">
				<div className="w-40">
					<Slider defaultValue={[40]} aria-label="One" />
				</div>
				<div className="w-40">
					<Slider defaultValue={[20, 70]} aria-label="Range" />
				</div>
				<div className="w-40">
					<Slider defaultValue={[60]} disabled aria-label="Disabled" />
				</div>
			</Row>
			<Row label="Toggle">
				<Toggle aria-label="Bold">
					<Bold />
				</Toggle>
				<Toggle aria-label="Italic" defaultPressed>
					<Italic />
				</Toggle>
				<Toggle variant="outline" aria-label="Underline">
					<Underline />
				</Toggle>
				<Toggle variant="outline" aria-label="Star" defaultPressed>
					<Star />
				</Toggle>
				<Toggle aria-label="Disabled" disabled>
					<Bold />
				</Toggle>
				<Toggle defaultPressed>Text on</Toggle>
			</Row>
		</Block>
	);
}

function Keys() {
	return (
		<Block title="Keys">
			<Row label="Kbd">
				<Kbd>⌘</Kbd>
				<Kbd>K</Kbd>
				<Kbd size="sm">Esc</Kbd>
				<Kbd variant="ghost">Enter</Kbd>
			</Row>
			<Row label="Shortcut">
				<Shortcut keys={["mod", "K"]} platform="mac" />
				<Shortcut keys={["mod", "shift", "R"]} platform="mac" />
				<Shortcut keys={["mod", "shift", "R"]} platform="other" />
				<Shortcut keys={["mod", "Enter"]} variant="ghost" platform="mac" />
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Controls",
	render: () => (
		<SinkPage title="Controls" description="Buttons, fields, choices and keys in every state.">
			<ThemePair>
				<Fields />
				<Buttons />
				<IconButtons />
				<Choices />
				<Keys />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Controls",
	parameters: sinkParameters,
};

export default meta;
