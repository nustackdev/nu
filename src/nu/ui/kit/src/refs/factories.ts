// Slice factories keyed by Ref type name.
//
// Split out of index.ts so the store can pull factories without also pulling
// in the React component graph. The individual ref modules still export a
// `RefEntry` bundle; here we lift the factory field only.

import { AreaChart } from "./chart/area-chart";
import { BarChart } from "./chart/bar-chart";
import { LineChart } from "./chart/line-chart";
import { PieChart } from "./chart/pie-chart";
import { Sparkline } from "./chart/sparkline";
import { ButtonRef } from "./input/button";
import { CheckboxRef } from "./input/checkbox";
import { DatePickerRef } from "./input/date-picker";
import { InputRef } from "./input/input";
import { NumberInputRef } from "./input/number-input";
import { RadioGroupRef } from "./input/radio-group";
import { SelectRef } from "./input/select";
import { SliderRef } from "./input/slider";
import { SwitchRef } from "./input/switch";
import { TagInputRef } from "./input/tag-input";
import { TextAreaRef } from "./input/text-area";
import { AccordionRef } from "./layout/accordion";
import { CardRef } from "./layout/card";
import { Column } from "./layout/column";
import { Container } from "./layout/container";
import { FieldRef } from "./layout/field";
import { Fieldset } from "./layout/fieldset";
import { Form } from "./layout/form";
import { Modal } from "./layout/modal";
import { Row } from "./layout/row";
import { TabsRef } from "./layout/tabs";
import { AlertRef } from "./output/alert";
import { BadgeRef } from "./output/badge";
import { CodeBlockRef } from "./output/code-block";
import { DividerRef } from "./output/divider";
import { GaugeRef } from "./output/gauge";
import { HeadingRef } from "./output/heading";
import { ImageRef } from "./output/image";
import { JsonViewerRef } from "./output/json-viewer";
import { LinkRef } from "./output/link";
import { MarkdownRef } from "./output/markdown";
import { ProgressRef } from "./output/progress";
import { StatRef } from "./output/stat";
import { TableRef } from "./output/table";
import { TextRef } from "./output/text";
import { NavRef } from "./structural/nav";
import { TitleRef } from "./structural/title";
import type { RefEntry, SliceFactory } from "./types";

// Single source of truth for the Ref registry. Ordered by kind for readability.
export const entries: Record<string, RefEntry> = {
	// Structural Refs (bound to browser APIs; no body output).
	TitleRef,
	NavRef,
	// Output Refs (server-owned sinks rendered in the body).
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
	// Chart Refs (output sinks with chart-specific payloads).
	LineChart,
	AreaChart,
	BarChart,
	PieChart,
	Sparkline,
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
};

export const factories: Record<string, SliceFactory> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.factory]),
);
