// Structural node types: bound to browser APIs. HistoryRef is the server's handle on History; NavItemRef is the one with
// body output: a link that reads the location to know when it is active.

import type { NodeEntry } from "../../tree";
import { HistoryRef } from "./history";
import { NavItemRef } from "./nav-item";
import { TitleRef } from "./title";

export const structuralEntries: Record<string, NodeEntry> = {
	TitleRef,
	HistoryRef,
	NavItemRef,
};
