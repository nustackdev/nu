// Input node types: tab-owned, the browser is source of truth.

import type { NodeEntry } from "../../tree";
import { ButtonRef } from "./button";
import { CheckboxRef } from "./checkbox";
import { DatePickerRef } from "./date-picker";
import { InputRef } from "./input";
import { NumberInputRef } from "./number-input";
import { ProseRef } from "./prose";
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
	ProseRef,
};
