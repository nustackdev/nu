// UploadFileRef and UploadFilesRef over the real tree store, with XHR mocked.
// A pick lands the value and a change, refusals (max_size, accept, max_files)
// say why under the control, and each command the program sends (pull,
// slice, cancel, discard, remove_file) answers with its notify: progress
// throttled, a slice of a landed file cached with no POST, a file changed on
// disk failing `unreadable` and struck in its row.

import { OPS, type TreeFrame } from "@nustackdev/ui-core";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

class FakeXHR {
	static all: FakeXHR[] = [];
	upload: { onprogress: ((e: Partial<ProgressEvent>) => void) | null } = { onprogress: null };
	onload: (() => void) | null = null;
	onerror: (() => void) | null = null;
	onabort: (() => void) | null = null;
	ontimeout: (() => void) | null = null;
	status = 0;
	responseText = "";
	method = "";
	url = "";
	body: Blob | null = null;
	aborted = false;
	open(method: string, url: string) {
		this.method = method;
		this.url = url;
	}
	send(body: Blob) {
		this.body = body;
		FakeXHR.all.push(this);
	}
	abort() {
		if (this.aborted) return;
		this.aborted = true;
		this.onabort?.();
	}
	progress(loaded: number, total: number) {
		this.upload.onprogress?.({ loaded, total, lengthComputable: true });
	}
	answer(status: number, body: unknown = {}) {
		this.status = status;
		this.responseText = JSON.stringify(body);
		this.onload?.();
	}
	fail() {
		this.onerror?.();
	}
}

let host: HTMLDivElement;
let root: Root;
let sent: TreeFrame[];
let now = 1_000;

beforeEach(() => {
	host = document.createElement("div");
	document.body.appendChild(host);
	root = createRoot(host);
	sent = [];
	FakeXHR.all = [];
	now = 1_000;
	vi.spyOn(Date, "now").mockImplementation(() => now);
	vi.stubGlobal("XMLHttpRequest", FakeXHR);
	tree.getState().setSender((frame) => sent.push(frame));
});

afterEach(() => {
	act(() => root.unmount());
	host.remove();
	tree.getState().remove([]);
	tree.getState().setSender(null);
	vi.unstubAllGlobals();
	vi.restoreAllMocks();
});

type Level = [string, string | null, Record<string, unknown>?];

function put(...chain: Level[]) {
	tree.getState().write(chain.map(([seg, type, props]) => [seg, type, props ?? {}]));
}

function draw(path: string[]) {
	act(() => root.render(<NodeView path={path} />));
}

function dispatch(path: string[], op: string, payload: unknown = null, id?: string) {
	act(() => tree.getState().dispatch({ op, ref: path, payload, id }));
}

async function settle() {
	await act(async () => {
		for (let i = 0; i < 10; i++) await Promise.resolve();
	});
}

const notifies = () =>
	sent.filter((f) => f.op === OPS.notify).map((f) => f.payload as Record<string, unknown>);
const events = (event: string) => notifies().filter((p) => p.event === event);
const valueAt = (path: string[]) => tree.getState().getIn(path)?.props.value;

function read(path: string[]): unknown {
	dispatch(path, OPS.read, null, "r");
	const last = sent.at(-1);
	expect(last).toMatchObject({ op: OPS.read, id: "r" });
	return last?.payload;
}

function file(name: string, bytes: number, type = "text/csv"): File {
	return new File(["x".repeat(bytes)], name, { type, lastModified: 42 });
}

/** A file changed on disk after the pick: every read of it fails. */
function gone(f: File): File {
	const bad = {
		size: f.size,
		slice: () => bad,
		arrayBuffer: () => Promise.reject(new DOMException("gone", "NotReadableError")),
	};
	f.slice = () => bad as unknown as Blob;
	return f;
}

function pickFiles(...files: File[]) {
	const input = host.querySelector<HTMLInputElement>('input[type="file"]');
	if (!input) throw new Error("no file input");
	Object.defineProperty(input, "files", { value: files, configurable: true });
	act(() => {
		input.dispatchEvent(new Event("change", { bubbles: true }));
	});
}

function dropFiles(...files: File[]) {
	const zone = host.querySelector('[data-slot="file-input"]');
	if (!zone) throw new Error("no drop zone");
	const ev = new Event("drop", { bubbles: true, cancelable: true });
	Object.defineProperty(ev, "dataTransfer", { value: { files } });
	act(() => {
		zone.dispatchEvent(ev);
	});
}

const URL = "/_nu/upload/sid1";
const one = (): Record<string, unknown> => valueAt(["n"]) as Record<string, unknown>;
const changes = () => events("change").length;

function picked(type = "UploadFileRef", props: Record<string, unknown> = {}, ...files: File[]) {
	put(["n", type, props]);
	draw(["n"]);
	pickFiles(...files);
}

describe("UploadFileRef: the selection", () => {
	it("reads null empty, lands a pick as the value with one change, no bytes moved", () => {
		put(["n", "UploadFileRef", { label: "Data" }]);
		draw(["n"]);
		expect(read(["n"])).toBeNull();
		const zone = host.querySelector("button[data-slot='file-input']");
		const label = host.querySelector("label");
		expect(label?.getAttribute("for")).toBe(zone?.id);
		pickFiles(file("orders.csv", 10));
		expect(one()).toMatchObject({
			name: "orders.csv",
			mime: "text/csv",
			size: 10,
			modified: 42,
			state: "picked",
			sent: 0,
			error: "",
		});
		expect(typeof one().key).toBe("string");
		expect(changes()).toBe(1);
		expect(FakeXHR.all).toHaveLength(0);
		expect(host.querySelector('[data-slot="file-row"]')?.textContent).toContain("orders.csv");
		expect(read(["n"])).toEqual(one());
	});

	it("replaces its file on a new pick, with a new key", () => {
		picked("UploadFileRef", {}, file("a.csv", 1));
		const first = one().key;
		pickFiles(file("b.csv", 2));
		expect(one()).toMatchObject({ name: "b.csv" });
		expect(one().key).not.toBe(first);
		expect(host.querySelectorAll('[data-slot="file-row"]')).toHaveLength(1);
	});

	it("draws the picked file in the zone's place, with Replace and remove", () => {
		put(["n", "UploadFileRef", { label: "Data" }]);
		draw(["n"]);
		pickFiles(file("a.csv", 1));
		expect(host.querySelector("button[data-slot='file-input']")).toBeNull();
		const replace = host.querySelector<HTMLButtonElement>('button[aria-label="Replace a.csv"]');
		expect(host.querySelector("label")?.getAttribute("for")).toBe(replace?.id);
		dropFiles(file("b.csv", 2));
		expect(one()).toMatchObject({ name: "b.csv" });
		const remove = host.querySelector<HTMLButtonElement>('button[aria-label="Remove b.csv"]');
		act(() => remove?.click());
		expect(valueAt(["n"])).toBeNull();
		expect(changes()).toBe(3);
		expect(host.querySelector("button[data-slot='file-input']")).not.toBeNull();
	});

	it("refuses a file over max_size at pick, with a message", () => {
		picked("UploadFileRef", { max_size: 5 }, file("big.csv", 9));
		expect(valueAt(["n"])).toBeUndefined();
		expect(changes()).toBe(0);
		const message = host.querySelector('[data-slot="field-error"]');
		expect(message?.textContent).toContain("big.csv");
		expect(message?.textContent).toContain("5 B");
		const zone = host.querySelector("button[data-slot='file-input']");
		expect(zone?.getAttribute("aria-describedby")?.split(" ")).toContain(message?.id);
	});

	it("checks accept on a drop", () => {
		put(["n", "UploadFileRef", { accept: ".csv,image/*" }]);
		draw(["n"]);
		dropFiles(file("x.txt", 1, "text/plain"));
		expect(valueAt(["n"])).toBeUndefined();
		expect(host.querySelector('[data-slot="field-error"]')?.textContent).toContain("x.txt");
		dropFiles(file("y.png", 1, "image/png"));
		expect(one()).toMatchObject({ name: "y.png" });
		expect(host.querySelector('[data-slot="field-error"]')).toBeNull();
	});

	it("takes chrome writes, never a value, and does nothing when disabled", () => {
		put(["n", "UploadFileRef", {}]);
		draw(["n"]);
		dispatch(["n"], OPS.write, { prompt: "Drop the csv", value: { name: "fake" } });
		expect(host.textContent).toContain("Drop the csv");
		expect(valueAt(["n"])).toBeUndefined();
		dispatch(["n"], OPS.write, { disabled: true });
		dropFiles(file("a.csv", 1));
		expect(valueAt(["n"])).toBeUndefined();
	});

	it("resets to nothing, aborting a running pull, and sends no change", async () => {
		picked("UploadFileRef", {}, file("a.csv", 100));
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		const xhr = FakeXHR.all[0];
		dispatch(["n"], "reset");
		await settle();
		expect(xhr.aborted).toBe(true);
		expect(valueAt(["n"])).toBeNull();
		expect(changes()).toBe(1);
		expect(events("upload")).toEqual([
			expect.objectContaining({ rid: "r1", state: "canceled", error: "canceled", token: null }),
		]);
		expect(host.querySelector('[data-slot="file-row"]')).toBeNull();
	});
});

describe("UploadFilesRef: the selection", () => {
	it("reads [] empty, appends a second pick, removes a row with a change", () => {
		put(["n", "UploadFilesRef", {}]);
		draw(["n"]);
		expect(read(["n"])).toEqual([]);
		pickFiles(file("a.csv", 1), file("b.csv", 2));
		dropFiles(file("c.csv", 3));
		const names = () => (valueAt(["n"]) as { name: string }[]).map((v) => v.name);
		expect(names()).toEqual(["a.csv", "b.csv", "c.csv"]);
		expect(changes()).toBe(2);
		const remove = host.querySelector<HTMLButtonElement>('button[aria-label="Remove b.csv"]');
		act(() => remove?.click());
		expect(names()).toEqual(["a.csv", "c.csv"]);
		expect(changes()).toBe(3);
	});

	it("cuts past max_files and says what it left out", () => {
		picked("UploadFilesRef", { max_files: 2 }, file("a.csv", 1));
		pickFiles(file("b.csv", 1), file("c.csv", 1));
		expect((valueAt(["n"]) as unknown[]).length).toBe(2);
		expect(host.querySelector('[data-slot="field-error"]')?.textContent).toContain("c.csv");
	});

	it("takes a paste on the focused zone", () => {
		put(["n", "UploadFilesRef", {}]);
		draw(["n"]);
		const zone = host.querySelector('[data-slot="file-input"]');
		const ev = new Event("paste", { bubbles: true, cancelable: true });
		Object.defineProperty(ev, "clipboardData", { value: { files: [file("p.csv", 4)] } });
		act(() => {
			zone?.dispatchEvent(ev);
		});
		expect((valueAt(["n"]) as { name: string }[]).map((v) => v.name)).toEqual(["p.csv"]);
	});

	it("lands in a Form's values, and a Form reset drops the handles with the value", async () => {
		put(["f", "Form", {}], ["up", "UploadFilesRef", {}]);
		draw(["f"]);
		pickFiles(file("a.csv", 1));
		dispatch(["f"], OPS.read, null, "fr");
		const values = sent.at(-1)?.payload as { up: { name: string }[] };
		expect(values.up.map((v) => v.name)).toEqual(["a.csv"]);
		dispatch(["f", "up"], "pull", { key: 0, rid: "r1", url: URL });
		dispatch(["f"], "reset");
		await settle();
		expect(valueAt(["f", "up"])).toEqual([]);
		expect(FakeXHR.all[0].aborted).toBe(true);
	});

	it("has no remove buttons when readonly", () => {
		picked("UploadFilesRef", {}, file("a.csv", 1));
		dispatch(["n"], OPS.write, { readonly: true });
		expect(host.querySelector('button[aria-label="Remove a.csv"]')).toBeNull();
		dropFiles(file("b.csv", 1));
		expect((valueAt(["n"]) as unknown[]).length).toBe(1);
	});

	it("names an entry by index or key, and pulls every file on a null key", async () => {
		picked("UploadFilesRef", {}, file("a.csv", 1), file("b.csv", 2));
		const [a, b] = valueAt(["n"]) as { key: string }[];
		dispatch(["n"], "pull", { key: 1, rid: "r1", url: URL });
		expect(FakeXHR.all).toHaveLength(1);
		expect(FakeXHR.all[0].body?.size).toBe(2);
		FakeXHR.all[0].answer(201, { token: "t".repeat(32), size: 2 });
		await settle();
		expect(events("upload")[0]).toMatchObject({ key: b.key, rid: "r1", state: "landed" });
		dispatch(["n"], "pull", { key: null, rid: "r2", url: URL });
		// b is landed and answers at once; a starts its own POST.
		expect(FakeXHR.all).toHaveLength(2);
		expect(events("upload")[1]).toMatchObject({ key: b.key, rid: "r2", state: "landed" });
		FakeXHR.all[1].answer(201, { token: "u".repeat(32), size: 1 });
		await settle();
		expect(events("upload")[2]).toMatchObject({ key: a.key, rid: "r2", token: "u".repeat(32) });
	});

	it("drops an entry on remove_file with no change, and cancels every pull on a null key", async () => {
		picked("UploadFilesRef", {}, file("a.csv", 1), file("b.csv", 2));
		const [a] = valueAt(["n"]) as { key: string }[];
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		dispatch(["n"], "cancel", { key: null });
		await settle();
		expect(FakeXHR.all.every((x) => x.aborted)).toBe(true);
		expect(events("upload").map((p) => p.state)).toEqual(["canceled", "canceled"]);
		dispatch(["n"], "remove_file", { key: a.key });
		expect((valueAt(["n"]) as { name: string }[]).map((v) => v.name)).toEqual(["b.csv"]);
		expect(changes()).toBe(1);
	});
});

describe("the zone", () => {
	function stray(type: "dragover" | "drop", at: Element): Event {
		const ev = new Event(type, { bubbles: true, cancelable: true });
		Object.defineProperty(ev, "dataTransfer", {
			value: { types: ["Files"], files: [file("s.csv", 1)], dropEffect: "" },
		});
		act(() => {
			at.dispatchEvent(ev);
		});
		return ev;
	}

	it("hints what it takes, out of the name and in the description", () => {
		put(["n", "UploadFileRef", { accept: ".csv,text/csv", max_size: 20_000_000 }]);
		draw(["n"]);
		const zone = host.querySelector("button[data-slot='file-input']");
		const hint = [...(zone?.querySelectorAll("[id]") ?? [])].find((el) =>
			el.textContent?.includes("CSV, up to 20 MB"),
		);
		expect(hint).toBeTruthy();
		expect(zone?.getAttribute("aria-describedby")?.split(" ")).toContain(hint?.id);
	});

	it("cancels a file dropped beside it, only while one is mounted", () => {
		put(["n", "UploadFilesRef", {}]);
		draw(["n"]);
		expect(stray("dragover", document.body).defaultPrevented).toBe(true);
		expect(stray("drop", document.body).defaultPrevented).toBe(true);
		act(() => root.unmount());
		root = createRoot(host);
		expect(stray("drop", document.body).defaultPrevented).toBe(false);
	});

	it("cancels a drop on a disabled zone without taking it", () => {
		put(["n", "UploadFilesRef", { disabled: true }]);
		draw(["n"]);
		const zone = host.querySelector("button[data-slot='file-input']");
		if (!zone) throw new Error("no zone");
		expect(stray("dragover", zone).defaultPrevented).toBe(true);
		expect(stray("drop", zone).defaultPrevented).toBe(true);
		expect(valueAt(["n"])).toBeUndefined();
	});
});

describe("commands", () => {
	it("pulls with throttled progress and answers landed with the token", async () => {
		picked("UploadFileRef", {}, file("a.csv", 1000));
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		const xhr = FakeXHR.all[0];
		expect(xhr.method).toBe("POST");
		expect(xhr.url).toBe(URL);
		expect(one()).toMatchObject({ state: "pulling" });
		act(() => xhr.progress(5, 1000)); // under 1%
		act(() => xhr.progress(100, 1000)); // moved 10%
		now += 50;
		act(() => xhr.progress(300, 1000)); // too soon
		now += 60;
		act(() => xhr.progress(305, 1000)); // 110 ms on, moved 20%
		expect(events("progress")).toEqual([
			{ event: "progress", key: one().key, rid: "r1", sent: 100, size: 1000 },
			{ event: "progress", key: one().key, rid: "r1", sent: 305, size: 1000 },
		]);
		act(() => xhr.answer(201, { token: "a".repeat(32), size: 1000 }));
		await settle();
		expect(events("upload")).toEqual([
			{
				event: "upload",
				key: one().key,
				rid: "r1",
				token: "a".repeat(32),
				state: "landed",
				size: 1000,
				error: "",
			},
		]);
		expect(one()).toMatchObject({ state: "landed", sent: 1000, error: "" });
		expect(changes()).toBe(1);
	});

	it("answers a pull of a landed file at once, and a pull of a running one when it ends", async () => {
		picked("UploadFileRef", {}, file("a.csv", 10));
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		dispatch(["n"], "pull", { key: null, rid: "r2", url: URL });
		expect(FakeXHR.all).toHaveLength(1);
		FakeXHR.all[0].answer(201, { token: "a".repeat(32), size: 10 });
		await settle();
		dispatch(["n"], "pull", { key: one().key, rid: "r3", url: URL });
		expect(FakeXHR.all).toHaveLength(1);
		expect(events("upload").map((p) => [p.rid, p.token])).toEqual([
			["r1", "a".repeat(32)],
			["r2", "a".repeat(32)],
			["r3", "a".repeat(32)],
		]);
	});

	it("posts a slice before the pull and answers cached once landed, with no POST", async () => {
		picked("UploadFileRef", {}, file("a.csv", 100));
		dispatch(["n"], "slice", { key: null, rid: "s1", url: URL, start: 10, end: 30 });
		expect(FakeXHR.all[0].body?.size).toBe(20);
		FakeXHR.all[0].answer(201, { token: "s".repeat(32), size: 20 });
		await settle();
		expect(events("slice")[0]).toEqual({
			event: "slice",
			key: one().key,
			rid: "s1",
			token: "s".repeat(32),
			cached: false,
			state: "landed",
			size: 20,
			error: "",
		});
		expect(one().state).toBe("picked");
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		FakeXHR.all[1].answer(201, { token: "a".repeat(32), size: 100 });
		await settle();
		dispatch(["n"], "slice", { key: null, rid: "s2", url: URL, start: 0, end: null });
		expect(FakeXHR.all).toHaveLength(2);
		expect(events("slice")[1]).toMatchObject({
			rid: "s2",
			token: "a".repeat(32),
			cached: true,
			state: "landed",
			size: 100,
		});
	});

	it("cancels a running pull: canceled answer, the file back to picked", async () => {
		picked("UploadFileRef", {}, file("a.csv", 10));
		dispatch(["n"], "cancel", { key: null }); // nothing runs: nothing happens
		expect(notifies().filter((p) => p.event !== "change")).toEqual([]);
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		dispatch(["n"], "cancel", { key: null });
		await settle();
		expect(events("upload")[0]).toMatchObject({ rid: "r1", state: "canceled", error: "canceled" });
		expect(one()).toMatchObject({ state: "picked", error: "canceled", sent: 0 });
	});

	it("discards a landed file: answers its token, and the next pull posts again", async () => {
		picked("UploadFileRef", {}, file("a.csv", 10));
		dispatch(["n"], "discard", { key: null, rid: "d0" });
		expect(events("discard")[0]).toEqual({
			event: "discard",
			key: one().key,
			rid: "d0",
			token: null,
		});
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		FakeXHR.all[0].answer(201, { token: "a".repeat(32), size: 10 });
		await settle();
		dispatch(["n"], "discard", { key: null, rid: "d1" });
		expect(events("discard")[1]).toMatchObject({ rid: "d1", token: "a".repeat(32) });
		expect(one()).toMatchObject({ state: "picked", sent: 0 });
		dispatch(["n"], "pull", { key: null, rid: "r2", url: URL });
		expect(FakeXHR.all).toHaveLength(2);
	});

	it("answers no_file when nothing is picked", () => {
		put(["n", "UploadFileRef", {}]);
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		dispatch(["n"], "slice", { key: null, rid: "s1", url: URL, start: 0, end: 4 });
		expect(events("upload")[0]).toMatchObject({ rid: "r1", state: "failed", error: "no_file" });
		expect(events("slice")[0]).toMatchObject({ rid: "s1", state: "failed", error: "no_file" });
		expect(FakeXHR.all).toHaveLength(0);
	});

	it("maps a file changed on disk to unreadable and strikes its row", async () => {
		picked("UploadFileRef", {}, gone(file("a.csv", 10)));
		dispatch(["n"], "pull", { key: null, rid: "r1", url: URL });
		FakeXHR.all[0].fail();
		await settle();
		expect(events("upload")[0]).toMatchObject({ rid: "r1", state: "failed", error: "unreadable" });
		expect(one()).toMatchObject({ state: "failed", error: "unreadable" });
		const row = host.querySelector('[data-slot="file-row"]');
		expect(row?.querySelector(".line-through")?.textContent).toBe("a.csv");
		expect(row?.textContent).toContain("Pick it again");
	});

	it("maps a dropped network, 413 and 403 to their codes", async () => {
		picked("UploadFileRef", {}, file("a.csv", 10));
		const codes: string[] = [];
		for (const end of [
			(x: FakeXHR) => x.fail(),
			(x: FakeXHR) => x.answer(413, { detail: "cap" }),
			(x: FakeXHR) => x.answer(403),
		]) {
			dispatch(["n"], "pull", { key: null, rid: "r", url: URL });
			const xhr = FakeXHR.all.at(-1);
			if (xhr) act(() => end(xhr));
			await settle();
			codes.push(String(events("upload").at(-1)?.error));
		}
		expect(codes).toEqual(["network", "too_large", "refused"]);
	});
});
