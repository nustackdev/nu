// Input node types: tab-owned, the browser is source of truth.

import type { NodeEntry } from "../../tree";
import { ButtonRef } from "./button";
import { CheckboxRef } from "./checkbox";
import { CodeRef } from "./code";
import { DatePickerRef } from "./date-picker";
import { InputRef } from "./input";
import { MarkdownRef } from "./markdown";
import { NumberInputRef } from "./number-input";
import { RadioGroupRef } from "./radio-group";
import { SelectRef } from "./select";
import { SliderRef } from "./slider";
import { SwitchRef } from "./switch";
import { TagInputRef } from "./tag-input";
import { TextAreaRef } from "./text-area";

export const inputEntries: Record<string, NodeEntry> = {
	InputRef,
	TextAreaRef,
	ButtonRef,
	CheckboxRef,
	SwitchRef,
	SelectRef,
	RadioGroupRef,
	SliderRef,
	NumberInputRef,
	DatePickerRef,
	TagInputRef,
	MarkdownRef,
	CodeRef,
};
