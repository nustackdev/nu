// History, the query encoding, the Router and the AnchorCatcher, on jsdom's
// real window.history.

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fixtures from "../../../../../tests/fixtures/query.json";
import {
	AnchorCatcher,
	type AnchorRule,
	catchAnchors,
	type Entry,
	History,
	type Move,
	matchRoute,
	mergeQuery,
	parseQuery,
	serializeQuery,
	useRoute,
} from ".";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

let moves: Move[];
let unsubscribe: () => void;

beforeEach(() => {
	window.history.replaceState(null, "", "/start");
	moves = [];
	unsubscribe = History.subscribe((m) => moves.push(m));
});

afterEach(() => {
	unsubscribe();
});

/** Run `go` and wait for the popstate it causes. */
function traversal(go: () => void): Promise<void> {
	return new Promise((resolve) => {
		window.addEventListener("popstate", () => resolve(), { once: true });
		go();
	});
}

describe("History", () => {
	it("pushes and replaces, announcing each move synchronously", () => {
		const depth = window.history.length;
		expect(History.push("/a?x=1#h", { k: 1 }, { origin: "me" })).toBe(true);
		expect(window.history.length).toBe(depth + 1);
		const entry = History.current();
		expect(entry).toEqual({
			url: "/a?x=1#h",
			path: "/a",
			query: { x: "1" },
			hash: "#h",
			state: { k: 1 },
		});
		expect(moves).toHaveLength(1);
		expect(moves[0]).toMatchObject({ kind: "push", source: "program", origin: "me" });
		expect(moves[0].previous.url).toBe("/start");
		History.replace("/b");
		expect(window.history.length).toBe(depth + 1);
		expect(History.current().state).toBeNull();
		expect(moves[1]).toMatchObject({ kind: "replace", source: "program", origin: undefined });
	});

	it("skips a move to the entry it is on, same url and same state", () => {
		History.push("/same", { a: [1, { b: 2 }] });
		const depth = window.history.length;
		expect(History.push("/same", { a: [1, { b: 2 }] })).toBe(false);
		expect(History.replace("/same", { a: [1, { b: 2 }] })).toBe(false);
		expect(window.history.length).toBe(depth);
		expect(moves).toHaveLength(1);
		expect(History.push("/same", { a: [1, { b: 3 }] })).toBe(true);
		expect(History.push("/same")).toBe(true);
		expect(moves).toHaveLength(3);
	});

	it("resolves a relative url against the page", () => {
		History.push("/docs/intro");
		History.push("guide?x=1");
		expect(History.current().url).toBe("/docs/guide?x=1");
	});

	it("keeps one snapshot per entry", () => {
		History.push("/snap", { s: 1 });
		expect(History.current()).toBe(History.current());
	});

	it("tags its own traversals and not the browser's", async () => {
		History.push("/one");
		await traversal(() => History.back({ origin: "mine" }));
		expect(window.location.pathname).toBe("/start");
		const own = moves.at(-1) as Move;
		expect(own).toMatchObject({ kind: "pop", source: "program", origin: "mine" });
		expect(own.previous.url).toBe("/one");
		await traversal(() => window.history.forward());
		expect(moves.at(-1)).toMatchObject({ kind: "pop", source: "browser", origin: undefined });
		expect(History.current().path).toBe("/one");
	});
});

describe("query encoding (shared fixtures)", () => {
	for (const { query, string } of fixtures.encode) {
		it(`encodes ${JSON.stringify(query)}`, () => {
			expect(serializeQuery(query)).toBe(string);
		});
	}
	for (const { string, query } of fixtures.decode) {
		it(`decodes ${JSON.stringify(string)}`, () => {
			expect(parseQuery(string)).toEqual(query);
		});
	}

	it("merges, dropping null keys", () => {
		expect(mergeQuery({ a: "1", b: "2" }, { b: null, c: 3, a: "x" })).toEqual({ a: "x", c: "3" });
	});
});

const at = (url: string): Entry => {
	const u = new URL(url, "http://localhost");
	return { url, path: u.pathname, query: parseQuery(u.search), hash: u.hash, state: null };
};

describe("matchRoute", () => {
	it("matches a pathname exactly, query and hash free", () => {
		const branches = ["/", "/feed", { path: "/about" }];
		expect(matchRoute(branches, at("/feed?x=1#y"))?.index).toBe(1);
		expect(matchRoute(branches, at("/feed/"))?.index).toBe(1);
		expect(matchRoute(branches, at("/"))?.index).toBe(0);
		expect(matchRoute(branches, at("/about"))?.branch).toEqual({ path: "/about" });
		expect(matchRoute(branches, at("/feed/more"))).toBeNull();
	});

	it("takes the first match, with a branch's own params", () => {
		const branches = [
			{ match: (e: Entry) => (e.path.startsWith("/movie/") ? { id: e.path.slice(7) } : null) },
			{ match: (e: Entry) => e.query.tab === "x" },
			"/movie/42",
		];
		expect(matchRoute(branches, at("/movie/42"))).toEqual({
			branch: branches[0],
			index: 0,
			params: { id: "42" },
		});
		expect(matchRoute(branches, at("/a?tab=x"))?.index).toBe(1);
		expect(matchRoute(branches, at("/a"))).toBeNull();
	});
});

describe("useRoute and AnchorCatcher", () => {
	let host: HTMLDivElement;
	let root: Root;

	beforeEach(() => {
		host = document.createElement("div");
		document.body.appendChild(host);
		root = createRoot(host);
	});

	afterEach(() => {
		act(() => root.unmount());
		host.remove();
	});

	const BRANCHES = ["/start", "/feed"];

	function Shown() {
		const match = useRoute(BRANCHES, "none");
		return <span data-testid="shown">{match === "none" ? "none" : match.branch}</span>;
	}

	const shown = () => host.querySelector("[data-testid=shown]")?.textContent;

	it("re-matches on every move, with a fallback", () => {
		act(() => root.render(<Shown />));
		expect(shown()).toBe("/start");
		act(() => {
			History.push("/feed?q=1");
		});
		expect(shown()).toBe("/feed");
		act(() => {
			History.push("/nowhere");
		});
		expect(shown()).toBe("none");
	});

	// Whether the catcher cancelled the click, read before jsdom gets to it:
	// the click is then cancelled anyway, since jsdom cannot navigate.
	function click(el: Element, init: MouseEventInit = {}): { defaultPrevented: boolean } {
		const e = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0, ...init });
		let prevented = false;
		const settle = (ev: Event) => {
			prevented = ev.defaultPrevented;
			ev.preventDefault();
		};
		document.addEventListener("click", settle, { once: true });
		act(() => {
			el.dispatchEvent(e);
		});
		document.removeEventListener("click", settle);
		return { defaultPrevented: prevented };
	}

	function links(html: string, rule?: AnchorRule) {
		act(() =>
			root.render(
				<AnchorCatcher rule={rule}>
					<div dangerouslySetInnerHTML={{ __html: html }} />
					<Shown />
				</AnchorCatcher>,
			),
		);
	}

	it("routes a plain in-app click through History", () => {
		links(`<a id="l" href="/feed?x=1"><span id="inner">Feed</span></a>`);
		const e = click(host.querySelector("#inner") as Element);
		expect(e.defaultPrevented).toBe(true);
		expect(History.current().url).toBe("/feed?x=1");
		expect(shown()).toBe("/feed");
	});

	it("leaves everything that is not a plain in-app link native", () => {
		links(
			[
				`<a id="ext" href="https://elsewhere.example/x">x</a>`,
				`<a id="blank" href="/feed" target="_blank">x</a>`,
				`<a id="dl" href="/feed" download>x</a>`,
				`<a id="mail" href="mailto:a@b.c">x</a>`,
				`<a id="frag" href="#cast">x</a>`,
				`<div contenteditable="true"><a id="edit" href="/feed">x</a></div>`,
				`<a id="ok" href="/feed">x</a>`,
			].join(""),
		);
		for (const id of ["ext", "blank", "dl", "mail", "frag", "edit"]) {
			expect(click(host.querySelector(`#${id}`) as Element).defaultPrevented).toBe(false);
		}
		const ok = host.querySelector("#ok") as Element;
		for (const mod of [{ metaKey: true }, { ctrlKey: true }, { shiftKey: true }, { button: 1 }]) {
			expect(click(ok, mod).defaultPrevented).toBe(false);
		}
		expect(History.current().path).toBe("/start");
		// Already handled by something under the catcher: left alone.
		ok.addEventListener("click", (ev) => ev.preventDefault(), { once: true });
		click(ok);
		expect(History.current().path).toBe("/start");
	});

	it("hands Option to the rule as alt, and leaves it native by default", () => {
		links(`<a id="l" href="/feed">x</a>`);
		const a = host.querySelector("#l") as Element;
		expect(click(a, { altKey: true }).defaultPrevented).toBe(false);
		expect(History.current().path).toBe("/start");

		const seen: [string, string][] = [];
		const rule: AnchorRule = (href, gesture) => {
			seen.push([href, gesture]);
			return gesture === "alt";
		};
		links(`<a id="l" href="/feed">x</a>`, rule);
		const b = host.querySelector("#l") as Element;
		expect(click(b, { altKey: true }).defaultPrevented).toBe(true);
		expect(click(b).defaultPrevented).toBe(false);
		expect(seen).toEqual([
			["/feed", "alt"],
			["/feed", "plain"],
		]);
	});

	it("takes Option+Enter on the link as alt, once, and no other key", () => {
		const seen: string[] = [];
		let take = true;
		const rule: AnchorRule = (href, gesture) => {
			seen.push(`${gesture} ${href}`);
			return take;
		};
		links(`<a id="l" href="/feed">x</a>`, rule);
		const a = host.querySelector("#l") as HTMLAnchorElement;
		const key = (init: KeyboardEventInit) => {
			const e = new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init });
			act(() => {
				a.dispatchEvent(e);
			});
			return e;
		};
		expect(key({ key: "Enter", altKey: true }).defaultPrevented).toBe(true);
		expect(seen).toEqual(["alt /feed"]);
		// Plain Enter is the browser's click, cmd+Enter and other keys are untouched.
		expect(key({ key: "Enter" }).defaultPrevented).toBe(false);
		expect(key({ key: "Enter", altKey: true, metaKey: true }).defaultPrevented).toBe(false);
		expect(key({ key: "a", altKey: true }).defaultPrevented).toBe(false);
		expect(seen).toEqual(["alt /feed"]);
		// Declined: the click the key fires next is not asked again.
		take = false;
		expect(key({ key: "Enter", altKey: true }).defaultPrevented).toBe(false);
		click(a, { altKey: true });
		expect(seen).toEqual(["alt /feed", "alt /feed"]);
	});

	it("cleans up", () => {
		const el = document.createElement("div");
		el.innerHTML = `<a id="c" href="/feed">x</a>`;
		document.body.appendChild(el);
		const stop = catchAnchors(el);
		stop();
		expect(click(el.querySelector("#c") as Element).defaultPrevented).toBe(false);
		el.remove();
	});
});
