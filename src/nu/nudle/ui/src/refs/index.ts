// Ref registry. One entry per Ref type module. Adding a new Ref type =
// drop a new module under refs/ and add one line here.

import type { ComponentType } from "react";
import { ButtonRef } from "./button";
import { InputRef } from "./input";
import { IntRef } from "./int";
import { LineChart } from "./line-chart";
import { TitleRef } from "./title";
import type { RefEntry, SliceFactory } from "./types";

const entries: Record<string, RefEntry> = {
	TitleRef,
	IntRef,
	LineChart,
	InputRef,
	ButtonRef,
};

export const factories: Record<string, SliceFactory> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.factory]),
);

export const renderers: Record<string, ComponentType<{ path: string }>> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.component]),
);

export type { RefEntry, RefSlice, SliceCtx, SliceFactory } from "./types";
