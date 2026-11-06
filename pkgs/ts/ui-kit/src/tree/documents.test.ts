// The document registry: handles by path, and the moment they appear.

import { describe, expect, it, vi } from "vitest";
import type { DocumentHandle } from "../lib/markdown/document";
import {
	documentPresent,
	documentUnder,
	registerDocument,
	registerPresence,
	subscribeDocuments,
	subscribePresence,
} from "./documents";

/** A handle that is only an identity; the registry never calls into it. */
function handle(name: string): DocumentHandle {
	return { name } as unknown as DocumentHandle;
}

describe("document registry", () => {
	it("finds the document at a path, or under it, and nothing elsewhere", () => {
		const a = handle("a");
		const leave = registerDocument(["cells", "1", "ui", "text"], a);
		expect(documentUnder(["cells", "1", "ui", "text"])).toBe(a);
		expect(documentUnder(["cells", "1", "ui"])).toBe(a);
		expect(documentUnder(["cells", "1"])).toBe(a);
		expect(documentUnder(["cells", "2"])).toBeNull();
		expect(documentUnder(["cells", "1", "ui", "text", "deeper"])).toBeNull();
		leave();
		expect(documentUnder(["cells", "1"])).toBeNull();
	});

	it("does not confuse a path with one that only starts the same way", () => {
		const leave = registerDocument(["cells", "10"], handle("ten"));
		expect(documentUnder(["cells", "1"])).toBeNull();
		leave();
	});

	it("tells a subscriber under a path when a document registers and leaves, and nobody else", () => {
		const here = vi.fn();
		const elsewhere = vi.fn();
		const everywhere = vi.fn();
		const stop = [
			subscribeDocuments(["cells", "1"], here),
			subscribeDocuments(["cells", "2"], elsewhere),
			subscribeDocuments(null, everywhere),
		];
		const a = handle("a");
		const leave = registerDocument(["cells", "1", "ui"], a);
		expect(here).toHaveBeenCalledWith(["cells", "1", "ui"], a);
		expect(everywhere).toHaveBeenCalledWith(["cells", "1", "ui"], a);
		expect(elsewhere).not.toHaveBeenCalled();
		leave();
		expect(here).toHaveBeenLastCalledWith(["cells", "1", "ui"], null);
		expect(everywhere).toHaveBeenLastCalledWith(["cells", "1", "ui"], null);
		for (const s of stop) s();
		registerDocument(["cells", "1", "ui"], a)();
		expect(here).toHaveBeenCalledTimes(2);
	});

	it("announces synchronously, inside the registration, so a parked request is consumed with no timing", () => {
		const seen: DocumentHandle[] = [];
		const stop = subscribeDocuments(["c"], (_path, h) => {
			if (h) seen.push(h);
		});
		const a = handle("a");
		const leave = registerDocument(["c", "doc"], a);
		expect(seen).toEqual([a]);
		leave();
		stop();
	});

	it("lets a remount replace the handle without the old unregister removing the new one", () => {
		const first = handle("first");
		const second = handle("second");
		const leaveFirst = registerDocument(["c"], first);
		const leaveSecond = registerDocument(["c"], second);
		expect(documentUnder(["c"])).toBe(second);
		leaveFirst();
		expect(documentUnder(["c"])).toBe(second);
		leaveSecond();
		expect(documentUnder(["c"])).toBeNull();
	});
});

describe("document presence", () => {
	it("is a separate question from taking commands", () => {
		const leave = registerPresence(["cells", "1", "ui", "text"]);
		expect(documentPresent(["cells", "1"])).toBe(true);
		expect(documentPresent(["cells", "2"])).toBe(false);
		expect(documentUnder(["cells", "1"])).toBeNull();
		const leaveDoc = registerDocument(["cells", "1", "ui", "text"], handle("a"));
		expect(documentUnder(["cells", "1"])).not.toBeNull();
		leaveDoc();
		expect(documentPresent(["cells", "1"])).toBe(true);
		leave();
		expect(documentPresent(["cells", "1"])).toBe(false);
	});

	it("tells a subscriber under a path when an editor appears and leaves", () => {
		const seen: boolean[] = [];
		const stop = subscribePresence(["c"], (_path, present) => seen.push(present));
		const docs = vi.fn();
		const stopDocs = subscribeDocuments(["c"], docs);
		const leave = registerPresence(["c", "doc"]);
		expect(seen).toEqual([true]);
		leave();
		expect(seen).toEqual([true, false]);
		expect(docs).not.toHaveBeenCalled();
		stop();
		stopDocs();
	});
});
