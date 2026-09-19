// The registry, and the registration side effect.
//
// This used to check parity against the flat store's `entries`. That list is
// gone, so the count stands in for it: 45 types shipped, and a type that
// quietly falls out of a barrel takes the count with it.

import { describe, expect, it } from "vitest";
import { registry } from "../tree";
import { nodeEntries } from ".";

describe("node registry", () => {
	it("ships every type", () => {
		expect(Object.keys(nodeEntries)).toHaveLength(45);
	});

	it("gives every type a component", () => {
		const missing = Object.entries(nodeEntries)
			.filter(([, entry]) => !entry.component)
			.map(([type]) => type);
		expect(missing).toEqual([]);
	});

	it("registers on import", () => {
		for (const type of Object.keys(nodeEntries)) {
			expect(registry[type]).toBe(nodeEntries[type]);
		}
	});
});
