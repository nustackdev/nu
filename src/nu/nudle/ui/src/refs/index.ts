// Ref registry. One entry per Ref type module. Adding a new Ref type =
// drop a new module under refs/ and add one line here.

import type { ComponentType } from "react";
import { BadgeRef } from "./badge";
import { ButtonRef } from "./button";
import { HeadingRef } from "./heading";
import { InputRef } from "./input";
import { IntRef } from "./int";
import { LineChart } from "./line-chart";
import { NavRef } from "./nav";
import { TableRef } from "./table";
import { TitleRef } from "./title";
import type { RefEntry, SliceFactory } from "./types";

const entries: Record<string, RefEntry> = {
	// Display Refs (rendered in the body).
	HeadingRef,
	IntRef,
	LineChart,
	InputRef,
	ButtonRef,
	BadgeRef,
	TableRef,
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
