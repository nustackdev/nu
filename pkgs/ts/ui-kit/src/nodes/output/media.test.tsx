// VideoRef and AudioRef over the real tree store, and the scrub bar under
// both: what each node draws from its props, the empty and fallback frames,
// and the slider semantics a screen reader and a keyboard get.

import { OPS } from "@nustackdev/ui-core";
import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { Scrubber } from "../../components/ui/media-controls";
import { NodeView, tree } from "../../tree";
import "..";

(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

// Radix measures the volume slider through ResizeObserver, which jsdom lacks.
globalThis.ResizeObserver ??= class {
	observe() {}
	unobserve() {}
	disconnect() {}
};

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
	tree.getState().remove([]);
});

function mount(type: string, props: Record<string, unknown>) {
	tree.getState().write([["n", type, props]]);
	act(() => root.render(<NodeView path={["n"]} />));
}

function dispatch(payload: unknown) {
	act(() => tree.getState().dispatch({ op: OPS.write, ref: ["n"], payload }));
}

const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);

describe("VideoRef", () => {
	it("draws a video with its poster, flags, ratio and corners", () => {
		mount("VideoRef", {
			src: "/clip.mp4",
			poster: "/still.jpg",
			aspect: "16:9",
			radius: "lg",
			fit: "cover",
			loop: true,
			muted: true,
		});
		const frame = slot("video");
		const video = host.querySelector("video");
		expect(video?.getAttribute("src")).toBe("/clip.mp4");
		expect(video?.getAttribute("poster")).toBe("/still.jpg");
		expect(video?.loop).toBe(true);
		expect(video?.muted).toBe(true);
		expect(video?.className).toContain("object-cover");
		expect(frame?.style.aspectRatio).toBe("16 / 9");
		expect(frame?.className).toContain("rounded-lg");
		expect(frame?.getAttribute("aria-roledescription")).toBe("video player");
		expect(frame?.tabIndex).toBe(0);
	});

	it("draws square corners and the transport until told otherwise", () => {
		mount("VideoRef", { src: "/clip.mp4" });
		expect(slot("video")?.className).toContain("rounded-none");
		expect(slot("video-controls")).not.toBeNull();
		expect(host.querySelector("[role=slider][aria-label=Seek]")).not.toBeNull();
	});

	it("says there is no video without a source, and swaps one in on a write", () => {
		mount("VideoRef", { src: "" });
		expect(host.querySelector("video")).toBeNull();
		expect(slot("empty-state")?.textContent).toContain("No video");
		dispatch({ src: "/b.mp4", width: 320 });
		expect(host.querySelector("video")?.getAttribute("src")).toBe("/b.mp4");
		expect(slot("video")?.style.width).toBe("320px");
	});
});

describe("AudioRef", () => {
	it("draws one row named by its title", async () => {
		mount("AudioRef", { src: "/a.mp3", title: "take-01.mp3", loop: true });
		const row = slot("audio");
		expect(row?.getAttribute("aria-label")).toBe("take-01.mp3");
		expect(slot("audio-title")?.textContent).toBe("take-01.mp3");
		expect(host.querySelector("audio")?.loop).toBe(true);
		expect(slot("media-play")?.getAttribute("aria-label")).toBe("Play");
		expect(slot("media-time")?.textContent).toBe("0:00 / --:--");
	});

	it("falls back to the plain bar where the waveform cannot decode", async () => {
		// jsdom has no Web Audio, so the decode comes back empty.
		mount("AudioRef", { src: "/a.mp3" });
		await act(async () => {
			await new Promise((r) => setTimeout(r, 0));
		});
		expect(slot("scrubber")).not.toBeNull();
		expect(slot("waveform")).toBeNull();
	});

	it("says there is no audio without a source", () => {
		mount("AudioRef", { title: "untitled" });
		expect(host.querySelector("audio")).toBeNull();
		expect(slot("audio")?.textContent).toContain("No audio");
		expect((slot("media-play") as HTMLButtonElement | null)?.disabled).toBe(true);
	});
});

describe("Scrubber", () => {
	function Harness() {
		const [t, setT] = useState(30);
		return <Scrubber time={t} duration={125} onSeek={setT} />;
	}

	const key = (el: Element, k: string, shift = false) =>
		act(() => {
			el.dispatchEvent(new KeyboardEvent("keydown", { key: k, shiftKey: shift, bubbles: true }));
		});

	it("is a slider that reads its time in words", () => {
		act(() => root.render(<Harness />));
		const s = slot("scrubber") as HTMLElement;
		expect(s.getAttribute("role")).toBe("slider");
		expect(s.getAttribute("aria-valuemax")).toBe("125");
		expect(s.getAttribute("aria-valuenow")).toBe("30");
		expect(s.getAttribute("aria-valuetext")).toBe("30 seconds of 2 minutes 5 seconds");
	});

	it("seeks on the arrows, shift, page keys, home and end", () => {
		act(() => root.render(<Harness />));
		const s = slot("scrubber") as HTMLElement;
		key(s, "ArrowRight");
		expect(s.getAttribute("aria-valuenow")).toBe("35");
		key(s, "ArrowLeft", true);
		expect(s.getAttribute("aria-valuenow")).toBe("20");
		key(s, "End");
		expect(s.getAttribute("aria-valuenow")).toBe("125");
		key(s, "PageDown");
		expect(s.getAttribute("aria-valuenow")).toBe("110");
		key(s, "Home");
		expect(s.getAttribute("aria-valuenow")).toBe("0");
	});

	it("is out of the tab order while the duration is unknown", () => {
		act(() => root.render(<Scrubber time={0} duration={Number.NaN} onSeek={() => {}} />));
		const s = slot("scrubber") as HTMLElement;
		expect(s.tabIndex).toBe(-1);
		expect(s.getAttribute("aria-disabled")).toBe("true");
		expect(s.getAttribute("aria-valuetext")).toBe("unknown");
	});
});
