// TableRef's two notifies: a header click and a row click, each naming its
// kind in `event` so the server's on_sort and on_row_click take only their own.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	tree.getState().setSender((frame) => sent.push(frame));
	tree
		.getState()
		.write([
			[
				"t",
				"TableRef",
				{ columns: ["title", "year"], rows: [["Arrival", 2016]], clickable_rows: true },
			],
		]);
	act(() => root.render(<NodeView path={["t"]} />));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
});

const notifies = () => sent.filter((f) => f.op === OPS.notify).map((f) => f.payload);

describe("TableRef", () => {
	it("names a header click a sort", () => {
		act(() => host.querySelector<HTMLElement>("th")?.click());
		expect(notifies()).toEqual([{ event: "sort", sort_column: "title", sort_direction: "asc" }]);
	});

	it("names a row click a row", () => {
		act(() => host.querySelector<HTMLElement>("tbody tr")?.click());
		expect(notifies()).toEqual([{ event: "row", row_index: 0 }]);
	});
});
