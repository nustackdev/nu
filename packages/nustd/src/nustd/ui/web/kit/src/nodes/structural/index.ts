// Structural node types: bound to browser APIs, no body output.

import type { NodeEntry } from "../../tree";
import { NavRef } from "./nav";
import { TitleRef } from "./title";

export const structuralEntries: Record<string, NodeEntry> = {
	TitleRef,
	NavRef,
};
