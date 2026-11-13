// Input node types: tab-owned, the browser is source of truth.

import type { NodeEntry } from "../../tree";
import { AutocompleteRef } from "./autocomplete";
import { ButtonRef } from "./button";
import { CheckboxRef } from "./checkbox";
import { CheckboxGroupRef } from "./checkbox-group";
import { CodeRef } from "./code";
import { ColorPickerRef } from "./color-picker";
import { DatePickerRef } from "./date-picker";
import { DateRangePickerRef } from "./date-range-picker";
import { DateTimePickerRef } from "./date-time-picker";
import { InlineEditRef } from "./inline-edit";
import { InputRef } from "./input";
import { MarkdownRef } from "./markdown";
import { MultiSelectRef } from "./multi-select";
import { NumberInputRef } from "./number-input";
import { RadioGroupRef } from "./radio-group";
import { RangeSliderRef } from "./range-slider";
import { SegmentedControlRef } from "./segmented-control";
import { SelectRef } from "./select";
import { SketchRef } from "./sketch";
import { SliderRef } from "./slider";
import { SwitchRef } from "./switch";
import { TagInputRef } from "./tag-input";
import { TextAreaRef } from "./text-area";
import { TimePickerRef } from "./time-picker";
import { ToggleRef } from "./toggle";

export const inputEntries: Record<string, NodeEntry> = {
	InputRef,
	InlineEditRef,
	TextAreaRef,
	ButtonRef,
	CheckboxRef,
	CheckboxGroupRef,
	SwitchRef,
	SelectRef,
	MultiSelectRef,
	AutocompleteRef,
	RadioGroupRef,
	SegmentedControlRef,
	SliderRef,
	RangeSliderRef,
	NumberInputRef,
	DatePickerRef,
	DateRangePickerRef,
	DateTimePickerRef,
	TimePickerRef,
	TagInputRef,
	MarkdownRef,
	CodeRef,
	ToggleRef,
	SketchRef,
	ColorPickerRef,
};
