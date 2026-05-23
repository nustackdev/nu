// Ref registry. One entry per Ref type module. Adding a new Ref type =
// drop a new module under refs/ and add one line here.

import type { ComponentType } from "react";
import { BadgeRef } from "./badge";
import { ButtonRef } from "./button";
import { CheckboxRef } from "./checkbox";
import { Column } from "./column";
import { Container } from "./container";
import { HeadingRef } from "./heading";
import { ImageRef } from "./image";
import { InputRef } from "./input";
import { JsonViewerRef } from "./json-viewer";
import { LineChart } from "./line-chart";
import { LinkRef } from "./link";
import { MarkdownRef } from "./markdown";
import { NavRef } from "./nav";
import { ProgressRef } from "./progress";
import { Row } from "./row";
import { SelectRef } from "./select";
import { SliderRef } from "./slider";
import { TableRef } from "./table";
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
	ImageRef,
	LinkRef,
	ProgressRef,
	LineChart,
	TableRef,
	JsonViewerRef,
	// Input Refs (tab-owned).
	InputRef,
	TextAreaRef,
	ButtonRef,
	CheckboxRef,
	SelectRef,
	SliderRef,
	// Layout Sections (Shape-based; wrap other Refs / Sections).
	Column,
	Row,
	Container,
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
