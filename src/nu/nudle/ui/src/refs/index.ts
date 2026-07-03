// Ref registry. One entry per Ref type module. Adding a new Ref type =
// drop a new module under refs/ and add one line here.

import type { ComponentType } from "react";
import { AccordionRef } from "./accordion";
import { AlertRef } from "./alert";
import { AreaChart } from "./area-chart";
import { BadgeRef } from "./badge";
import { BarChart } from "./bar-chart";
import { ButtonRef } from "./button";
import { CardRef } from "./card";
import { CheckboxRef } from "./checkbox";
import { CodeBlockRef } from "./code-block";
import { Column } from "./column";
import { Container } from "./container";
import { DatePickerRef } from "./date-picker";
import { DividerRef } from "./divider";
import { FieldRef } from "./field";
import { Fieldset } from "./fieldset";
import { Form } from "./form";
import { GaugeRef } from "./gauge";
import { HeadingRef } from "./heading";
import { ImageRef } from "./image";
import { InputRef } from "./input";
import { JsonViewerRef } from "./json-viewer";
import { LineChart } from "./line-chart";
import { LinkRef } from "./link";
import { MarkdownRef } from "./markdown";
import { Modal } from "./modal";
import { NavRef } from "./nav";
import { NumberInputRef } from "./number-input";
import { PieChart } from "./pie-chart";
import { ProgressRef } from "./progress";
import { RadioGroupRef } from "./radio-group";
import { Row } from "./row";
import { SelectRef } from "./select";
import { SliderRef } from "./slider";
import { Sparkline } from "./sparkline";
import { StatRef } from "./stat";
import { SwitchRef } from "./switch";
import { TableRef } from "./table";
import { TabsRef } from "./tabs";
import { TagInputRef } from "./tag-input";
import { TextRef } from "./text";
import { TextAreaRef } from "./text-area";
import { TitleRef } from "./title";
import type { RefEntry, SliceFactory } from "./types";

const entries: Record<string, RefEntry> = {
	// Display Refs (rendered in the body).
	HeadingRef,
	TextRef,
	MarkdownRef,
	BadgeRef,
	AlertRef,
	StatRef,
	DividerRef,
	CodeBlockRef,
	ImageRef,
	LinkRef,
	ProgressRef,
	GaugeRef,
	LineChart,
	AreaChart,
	BarChart,
	PieChart,
	Sparkline,
	TableRef,
	JsonViewerRef,
	// Input Refs (tab-owned).
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
	// Layout Sections (Shape-based; wrap other Refs / Sections).
	Column,
	Row,
	Container,
	Form,
	Fieldset,
	FieldRef,
	CardRef,
	TabsRef,
	AccordionRef,
	Modal,
	// Structural Refs (bound to browser APIs; no body output).
	TitleRef,
	NavRef,
};

export const factories: Record<string, SliceFactory> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.factory]),
);

export const renderers: Record<string, ComponentType<{ path: string }>> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.component]),
);

export type { RefEntry, RefSlice, SliceCtx, SliceFactory } from "./types";
