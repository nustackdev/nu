// SelectRef -- single-select dropdown. Browser is source of truth.
//
// The picked option's value is the node's `value` ("" for none). A pick lands
// it and sends `{event: "change"}` at once (./control.ts). A bare write
// selects (nil clears); an object payload merges into props the way the store
// merges everything else, which is how `options` gets replaced. The store
// answers a read from `value`, and `reset` puts the declared value back.
//
// Options arrive raw off the wire (strings or {value,label} maps) and are
// normalized at render rather than in a factory. Composes the kit Select
// primitive (Radix Select) so the popover reads through tokens on both
// themes; native <select> is dropped.
//
// `searchable` swaps the picker for the kit Combobox, a filter field over
// the same options (matching value or label). Value, notify and read stay
// the same, so the server cannot tell the two apart. The entry is `fill`:
// a select has no intrinsic width, so in a Row it takes a share of the free
// width.

import { useMemo } from "react";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "../../components/ui/combobox";
import { Label } from "../../components/ui/field";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "../../components/ui/select";
import {
	type NodeEntry,
	type NodeProps,
	useBoolProp,
	useListProp,
	useStringProp,
} from "../../tree";
import { asText, type Control, resetHandler, useCommit, useControl, valueWrite } from "./control";

export type Option = { value: string; label: string };

export function normalizeOptions(raw: unknown[]): Option[] {
	const out: Option[] = [];
	for (const item of raw) {
		if (typeof item === "string") {
			out.push({ value: item, label: item });
		} else if (item && typeof item === "object") {
			const o = item as { value?: unknown; label?: unknown };
			const value = o.value == null ? "" : String(o.value);
			const label = o.label == null ? value : String(o.label);
			out.push({ value, label });
		}
	}
	return out;
}

function SelectView({ path }: NodeProps) {
	const selected = useStringProp(path, "value");
	const searchable = useBoolProp(path, "searchable");
	const rawOptions = useListProp<unknown>(path, "options");
	const options = useMemo(() => normalizeOptions(rawOptions), [rawOptions]);
	const c = useControl(path);
	const { pick } = useCommit(path);
	const Picker = searchable ? SearchPicker : PlainPicker;
	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<Picker
				control={c}
				selected={selected}
				options={options}
				onPick={(next) => {
					if (!c.readOnly) pick(next);
				}}
			/>
		</div>
	);
}

type PickerProps = {
	control: Control;
	selected: string;
	options: Option[];
	onPick: (value: string) => void;
};

function PlainPicker({ control: c, selected, options, onPick }: PickerProps) {
	return (
		<Select value={selected} onValueChange={onPick} disabled={c.disabled} required={c.required}>
			<SelectTrigger
				{...c.aria}
				size={c.size}
				invalid={c.invalid}
				autoFocus={c.autoFocus}
				aria-readonly={c.readOnly || undefined}
			>
				<SelectValue placeholder={c.placeholder} />
			</SelectTrigger>
			<SelectContent>
				{options.map((o) => (
					<SelectItem key={o.value} value={o.value}>
						{o.label}
					</SelectItem>
				))}
			</SelectContent>
		</Select>
	);
}

// cmdk filters on an item's value plus its keywords, so the label rides as a
// keyword and typing either one finds the option.
function SearchPicker({ control: c, selected, options, onPick }: PickerProps) {
	const current = options.find((o) => o.value === selected);
	return (
		<Combobox value={selected} onValueChange={onPick}>
			<ComboboxTrigger
				{...c.aria}
				size={c.size}
				invalid={c.invalid}
				disabled={c.disabled}
				autoFocus={c.autoFocus}
				aria-readonly={c.readOnly || undefined}
				data-placeholder={current ? undefined : ""}
			>
				<span>{current ? current.label : c.placeholder}</span>
			</ComboboxTrigger>
			<ComboboxContent>
				<ComboboxInput placeholder="Search" />
				<ComboboxList>
					<ComboboxEmpty>No match</ComboboxEmpty>
					{options.map((o) => (
						<ComboboxItem key={o.value} value={o.value} keywords={[o.label]}>
							{o.label}
						</ComboboxItem>
					))}
				</ComboboxList>
			</ComboboxContent>
		</Combobox>
	);
}

export const SelectRef: NodeEntry = {
	component: SelectView,
	fill: true,
	input: { empty: "" },
	handlers: {
		write: valueWrite(asText),
		reset: resetHandler,
	},
};
