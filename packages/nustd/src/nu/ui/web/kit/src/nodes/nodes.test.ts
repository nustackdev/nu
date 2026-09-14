// Parity with the old registry, and the registration side effect.
//
// The flat store's `entries` is the list the apps run on today. Until it goes
// away, every type in it has to exist here too, or a page that renders fine
// on the old store would come up with holes on the tree store.

import { describe, expect, it } from "vitest";
import { entries } from "../refs";
import { registry } from "../tree";
import { nodeEntries } from ".";

describe("node registry", () => {
	it("covers every type the old registry has", () => {
		expect(Object.keys(nodeEntries).sort()).toEqual(Object.keys(entries).sort());
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
