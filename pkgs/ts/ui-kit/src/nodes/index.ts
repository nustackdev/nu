// Every node type the kit ships, registered on import.
//
// The registry is closed by default: adding a type means dropping a module
// under one of the group folders and adding a line to that group's barrel.
// `containers/` holds the types with open-ended children (Row, Card, ...);
// every other group holds leaves, drawn from their own props.
// A type that lives in a downstream package (nuspace, an app) calls
// `register` from the tree barrel at boot instead.

import { type NodeEntry, register } from "../tree";
import { chartEntries } from "./chart";
import { containerEntries } from "./containers";
import { inputEntries } from "./input";
import { outputEntries } from "./output";
import { structuralEntries } from "./structural";

export const nodeEntries: Record<string, NodeEntry> = {
	...structuralEntries,
	...outputEntries,
	...inputEntries,
	...chartEntries,
	...containerEntries,
};

for (const [type, entry] of Object.entries(nodeEntries)) register(type, entry);
