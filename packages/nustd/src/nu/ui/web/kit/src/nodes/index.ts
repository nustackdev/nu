// Every node type the kit ships, registered on import.
//
// The registry is closed by default: adding a type means dropping a module
// under one of the group folders and adding a line to that group's barrel.
// A type that lives in a downstream package (nuspace, an app) calls
// `register` from the tree barrel at boot instead.

import { type NodeEntry, register } from "../tree";
import { chartEntries } from "./chart";
import { inputEntries } from "./input";
import { layoutEntries } from "./layout";
import { outputEntries } from "./output";
import { structuralEntries } from "./structural";

export const nodeEntries: Record<string, NodeEntry> = {
	...structuralEntries,
	...outputEntries,
	...inputEntries,
	...chartEntries,
	...layoutEntries,
};

for (const [type, entry] of Object.entries(nodeEntries)) register(type, entry);
