// postFile against a mocked XHR: the pieces it cuts and the query each one
// names, a dropped piece sent again from the same offset, a 409 resuming from
// what the server has, giving up after its tries, and an abort mid pause.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { postFile } from "./transfer";

class FakeXHR {
	static all: FakeXHR[] = [];
	upload: { onprogress: ((e: Partial<ProgressEvent>) => void) | null } = { onprogress: null };
	onload: (() => void) | null = null;
	onerror: (() => void) | null = null;
	onabort: (() => void) | null = null;
	ontimeout: (() => void) | null = null;
	status = 0;
	responseText = "";
	url = "";
	body: Blob | null = null;
	open(_method: string, url: string) {
		this.url = url;
	}
	send(body: Blob) {
		this.body = body;
		FakeXHR.all.push(this);
	}
	abort() {
		this.onabort?.();
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

const T = "a".repeat(32);
const last = () => {
	const xhr = FakeXHR.all.at(-1);
	if (!xhr) throw new Error("nothing sent");
	return xhr;
};
const query = (xhr: FakeXHR) => xhr.url.slice(xhr.url.indexOf("?") + 1);
const flush = () => vi.advanceTimersByTimeAsync(0);

beforeEach(() => {
	FakeXHR.all = [];
	vi.useFakeTimers();
	vi.stubGlobal("XMLHttpRequest", FakeXHR);
});

afterEach(() => {
	vi.useRealTimers();
	vi.unstubAllGlobals();
});

describe("postFile", () => {
	it("sends a small file as one piece that names its total", async () => {
		const t = postFile("/_nu/upload/s", new Blob(["hello"]));
		expect(last().url).toBe("/_nu/upload/s?total=5");
		expect(last().body?.size).toBe(5);
		last().answer(201, { token: T, size: 5 });
		expect(await t.done).toEqual({ token: T, size: 5, error: "" });
	});

	it("cuts a file into pieces by offset and adds their progress up", async () => {
		const seen: number[] = [];
		const t = postFile("/u", new Blob(["x".repeat(10)]), (sent) => seen.push(sent), { piece: 4 });
		last().answer(202, { token: T, size: 4 });
		await flush();
		expect(query(last())).toBe(`token=${T}&offset=4&total=10`);
		last().upload.onprogress?.({ loaded: 3 });
		last().answer(202, { token: T, size: 8 });
		await flush();
		expect(query(last())).toBe(`token=${T}&offset=8&total=10`);
		expect(last().body?.size).toBe(2);
		last().answer(201, { token: T, size: 10 });
		expect(await t.done).toEqual({ token: T, size: 10, error: "" });
		expect(FakeXHR.all.map((x) => x.body?.size)).toEqual([4, 4, 2]);
		expect(seen).toContain(7);
	});

	it("sends a dropped piece again from the same offset after a pause", async () => {
		const t = postFile("/u", new Blob(["x".repeat(8)]), undefined, { piece: 4, wait: 100 });
		last().answer(202, { token: T, size: 4 });
		await flush();
		last().fail();
		await flush();
		expect(FakeXHR.all).toHaveLength(2); // still waiting
		await vi.advanceTimersByTimeAsync(100);
		expect(FakeXHR.all).toHaveLength(3);
		expect(query(last())).toBe(`token=${T}&offset=4&total=8`);
		last().answer(201, { token: T, size: 8 });
		expect(await t.done).toMatchObject({ token: T, error: "" });
	});

	it("goes on from the size a 409 says the server has", async () => {
		const t = postFile("/u", new Blob(["x".repeat(12)]), undefined, { piece: 4 });
		last().answer(202, { token: T, size: 4 });
		await flush();
		last().answer(409, { token: T, size: 2 });
		await flush();
		expect(query(last())).toBe(`token=${T}&offset=2&total=12`);
		expect(last().body?.size).toBe(4);
		t.abort();
		expect(await t.done).toMatchObject({ token: null, error: "canceled" });
	});

	it("gives up as network after its tries", async () => {
		const t = postFile("/u", new Blob(["abc"]), undefined, { tries: 3, wait: 10 });
		for (let i = 0; i < 3; i++) {
			last().fail();
			await vi.advanceTimersByTimeAsync(1_000);
		}
		expect(FakeXHR.all).toHaveLength(3);
		expect(await t.done).toEqual({ token: null, size: 3, error: "network" });
	});

	it("stops at once when aborted during a pause", async () => {
		const t = postFile("/u", new Blob(["abc"]), undefined, { wait: 10_000 });
		last().fail();
		await flush();
		t.abort();
		expect(await t.done).toMatchObject({ error: "canceled" });
		await vi.advanceTimersByTimeAsync(60_000);
		expect(FakeXHR.all).toHaveLength(1);
	});

	it("maps a 413 on the first piece to too_large", async () => {
		const t = postFile("/u", new Blob(["abc"]));
		last().answer(413, "cap");
		expect(await t.done).toEqual({ token: null, size: 3, error: "too_large" });
	});

	it("maps a 507, a server out of disk, to no_space", async () => {
		const t = postFile("/u", new Blob(["abc"]));
		last().answer(507, "full");
		expect(await t.done).toEqual({ token: null, size: 3, error: "no_space" });
	});
});
