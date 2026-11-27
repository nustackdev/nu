// ImageRef, VideoRef, AudioRef and FileRef over the real tree store, and the scrub
// bar under video and audio: what each node draws from its props, the empty and fallback frames,
// and the slider semantics a screen reader and a keyboard get.

import { OPS } from "@nustackdev/ui-core";
import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fileGlyph, fileName, fileType } from "../../components/ui/file";
import { MediaControls, Scrubber } from "../../components/ui/media-controls";
import { EMPTY_SNAPSHOT, type MediaApi, type MediaSnapshot } from "../../lib/media/use-media";
import { TouchProvider } from "../../lib/touch";
import { NodeView, tree } from "../../tree";
import "..";
import { normAspect } from "./image";

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

function mount(type: string, props: Record<string, unknown>, touch?: boolean) {
	tree.getState().write([["n", type, props]]);
	const view = <NodeView path={["n"]} />;
	act(() =>
		root.render(touch === undefined ? view : <TouchProvider value={touch}>{view}</TouchProvider>),
	);
}

function dispatch(payload: unknown) {
	act(() => tree.getState().dispatch({ op: OPS.write, ref: ["n"], payload }));
}

const slot = (name: string) => host.querySelector<HTMLElement>(`[data-slot=${name}]`);
const cls = (el: Element | null) => el?.className.split(/\s+/) ?? [];

describe("ImageRef", () => {
	it("draws square corners until a radius is set", () => {
		mount("ImageRef", { src: "/a.png" });
		expect(cls(slot("image"))).not.toContain("rounded-md");
		dispatch({ radius: "full" });
		expect(cls(slot("image"))).toContain("rounded-full");
	});

	it("holds an aspect ratio and takes the full width for it", () => {
		mount("ImageRef", { src: "/a.png", aspect: "16:9", fit: "scale-down" });
		const img = slot("image");
		expect(img?.style.aspectRatio).toBe("16 / 9");
		expect(img?.style.width).toBe("100%");
		expect(cls(img)).toContain("object-scale-down");
	});

	it("draws a viewer with zoom on, 320px tall unless sized", () => {
		mount("ImageRef", { src: "/a.png", zoom: true });
		const viewer = slot("image-viewer");
		expect(viewer).not.toBeNull();
		expect(slot("image")).toBeNull();
		expect(cls(viewer)).toContain("h-80");
		dispatch({ aspect: "4:3" });
		expect(slot("image-viewer")?.style.aspectRatio).toBe("4 / 3");
		expect(cls(slot("image-viewer"))).not.toContain("h-80");
		dispatch({ height: 200 });
		expect(slot("image-viewer")?.style.height).toBe("200px");
		dispatch({ zoom: false });
		expect(slot("image-viewer")).toBeNull();
		expect(slot("image")).not.toBeNull();
	});

	it("fits a small image, zooms by key and goes pixelated past 1:1", () => {
		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			mount("ImageRef", { src: "/sprite.png", alt: "Sprite", zoom: true });
			const img = slot("image-viewer-stage")?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 16 });
			Object.defineProperty(img, "naturalHeight", { value: 16 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			const zoom = () => slot("image-viewer-zoom")?.textContent;
			expect(zoom()).toBe("1875%");
			expect(img.style.width).toBe("300px");
			expect(img.style.imageRendering).toBe("pixelated");

			const stage = slot("image-viewer-stage") as HTMLElement;
			expect(stage.getAttribute("aria-label")).toBe("Sprite");
			const key = (k: string) =>
				act(() => {
					stage.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true }));
				});
			key("1");
			expect(zoom()).toBe("100%");
			expect(img.style.imageRendering).toBe("");
			key("+");
			expect(zoom()).toBe("150%");
			key("0");
			expect(zoom()).toBe("1875%");

			const labels = [...(slot("image-viewer-controls")?.querySelectorAll("button") ?? [])].map(
				(b) => b.getAttribute("aria-label"),
			);
			expect(labels).toEqual(["Zoom out", "Zoom in", "Fit", "Actual size", "Full screen"]);
			const fit = slot("image-viewer-controls")?.querySelector('[aria-label="Fit"]');
			expect(fit?.getAttribute("aria-disabled")).toBe("true");
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("opens full window with the exit where full screen was, and a solid close", () => {
		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			mount("ImageRef", { src: "/a.png", alt: "Shot", zoom: true });
			const img = slot("image-viewer-stage")?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 800 });
			Object.defineProperty(img, "naturalHeight", { value: 600 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			const full = host.querySelector<HTMLElement>('[aria-label="Full screen"]');
			act(() => full?.click());
			const overlay = document.querySelector<HTMLElement>("[data-slot=image-viewer-overlay]");
			expect(overlay).not.toBeNull();
			// The full window viewer is its own viewer: its image loads again.
			const inner = overlay?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(inner, "naturalWidth", { value: 800 });
			Object.defineProperty(inner, "naturalHeight", { value: 600 });
			act(() => {
				inner.dispatchEvent(new Event("load"));
			});
			const cluster = overlay?.querySelector("[data-slot=image-viewer-controls]");
			const last = [...(cluster?.querySelectorAll("button") ?? [])].at(-1);
			expect(last?.getAttribute("aria-label")).toBe("Exit full screen");
			// 20px in from the corner, plus the safe area on a phone.
			expect(cls(cluster ?? null)).toEqual(
				expect.arrayContaining([
					"right-[calc(1.25rem+env(safe-area-inset-right))]",
					"bottom-[calc(1.25rem+env(safe-area-inset-bottom))]",
				]),
			);
			const close = overlay?.querySelector("[data-slot=image-viewer-close]");
			expect(close?.getAttribute("aria-label")).toBe("Close");
			expect(cls(close ?? null)).toEqual(
				expect.arrayContaining([
					"top-[calc(1.25rem+env(safe-area-inset-top))]",
					"right-[calc(1.25rem+env(safe-area-inset-right))]",
				]),
			);
			const stage = overlay?.querySelector("[data-slot=image-viewer-stage]") as HTMLElement;
			act(() => {
				stage.dispatchEvent(new KeyboardEvent("keydown", { key: "f", bubbles: true }));
			});
			expect(document.querySelector("[data-slot=image-viewer-overlay]")).toBeNull();
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("shows the download chip and the zoom cluster at rest in touch mode, hover only otherwise", () => {
		mount("ImageRef", { src: "/a.png", alt: "Shot", download: "/a.png?download=1" });
		expect(cls(slot("media-download"))).toContain("opacity-0");
		act(() => root.unmount());
		tree.getState().remove([]);
		root = createRoot(host);
		mount("ImageRef", { src: "/a.png", alt: "Shot", download: "/a.png?download=1" }, true);
		expect(cls(slot("media-download"))).not.toContain("opacity-0");

		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			act(() => root.unmount());
			tree.getState().remove([]);
			root = createRoot(host);
			mount("ImageRef", { src: "/a.png", alt: "Shot", zoom: true }, true);
			const img = slot("image-viewer-stage")?.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 800 });
			Object.defineProperty(img, "naturalHeight", { value: 600 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			expect(cls(slot("image-viewer-controls"))).not.toContain("opacity-0");
			// At fit a finger still scrolls the page; the pinch is the viewer's.
			expect(cls(slot("image-viewer-stage"))).toEqual(
				expect.arrayContaining(["touch-pan-x", "touch-pan-y"]),
			);
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("pinches with two fingers and toggles fit on a double tap, in touch mode", () => {
		const w = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(400);
		const h = vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockReturnValue(300);
		try {
			mount("ImageRef", { src: "/a.png", alt: "Shot", zoom: true }, true);
			const stage = slot("image-viewer-stage") as HTMLElement;
			const img = stage.querySelector("img") as HTMLImageElement;
			Object.defineProperty(img, "naturalWidth", { value: 800 });
			Object.defineProperty(img, "naturalHeight", { value: 600 });
			act(() => {
				img.dispatchEvent(new Event("load"));
			});
			stage.setPointerCapture ??= () => {};
			const touch = (type: string, id: number, x: number, y = 100) =>
				act(() => {
					stage.dispatchEvent(
						new PointerEvent(type, {
							bubbles: true,
							pointerType: "touch",
							pointerId: id,
							clientX: x,
							clientY: y,
						}),
					);
				});
			const zoom = () => slot("image-viewer-zoom")?.textContent;
			expect(zoom()).toBe("50%");
			// Fingers 100px apart spread to 200px: twice the scale.
			touch("pointerdown", 1, 100);
			touch("pointerdown", 2, 200);
			touch("pointermove", 2, 300);
			expect(zoom()).toBe("100%");
			touch("pointerup", 2, 300);
			touch("pointerup", 1, 100);
			// A double tap from a zoom goes back to fit, then in again.
			touch("pointerdown", 3, 150);
			touch("pointerup", 3, 150);
			touch("pointerdown", 4, 152);
			touch("pointerup", 4, 152);
			expect(zoom()).toBe("50%");
		} finally {
			w.mockRestore();
			h.mockRestore();
		}
	});

	it("reads the aspect spellings", () => {
		expect(normAspect("4/3")).toBe("4 / 3");
		expect(normAspect("1.5")).toBe("1.5");
		expect(normAspect("")).toBeUndefined();
		expect(normAspect("wide")).toBeUndefined();
		expect(normAspect("1/0")).toBeUndefined();
	});
});

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

	it("keeps the transport up while playing in touch mode, where nothing hovers", () => {
		const play = () => {
			const v = host.querySelector("video") as HTMLVideoElement;
			Object.defineProperty(v, "paused", { value: false, configurable: true });
			act(() => {
				v.dispatchEvent(new Event("play"));
			});
		};
		mount("VideoRef", { src: "/clip.mp4" });
		play();
		expect(slot("video")?.dataset.state).toBe("playing");
		expect(slot("video-controls")?.hasAttribute("data-shown")).toBe(false);
		act(() => root.unmount());
		tree.getState().remove([]);
		root = createRoot(host);
		mount("VideoRef", { src: "/clip.mp4" }, true);
		play();
		expect(slot("video")?.dataset.state).toBe("playing");
		expect(slot("video-controls")?.hasAttribute("data-shown")).toBe(true);
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

describe("FileRef", () => {
	it("draws the name, size and type, opened in a new tab", () => {
		mount("FileRef", {
			src: "/blobs/abc",
			name: "report.pdf",
			size: 48_200,
			mime: "application/pdf",
			download: "/blobs/abc?download=1",
		});
		const link = slot("file-link") as HTMLAnchorElement | null;
		expect(link?.getAttribute("href")).toBe("/blobs/abc");
		expect(link?.getAttribute("target")).toBe("_blank");
		expect(slot("file-name")?.textContent).toBe("report.pdf");
		expect(slot("file-meta")?.textContent).toBe("48.2 KB · PDF");
		expect(slot("media-download")?.getAttribute("href")).toBe("/blobs/abc?download=1");
	});

	it("reads the url's last part without a name, and drops what it lacks", () => {
		mount("FileRef", { src: "/files/notes%20v2.txt?x=1" });
		expect(slot("file-name")?.textContent).toBe("notes v2.txt");
		expect(slot("file-meta")).toBeNull();
		expect(slot("media-download")).toBeNull();
	});

	it("is muted and inert without a source until one lands", () => {
		mount("FileRef", { name: "later.csv", download: "/d" });
		expect(slot("file")?.dataset.empty).toBe("true");
		expect(slot("file-link")).toBeNull();
		expect(slot("media-download")).toBeNull();
		expect(slot("file-name")?.textContent).toBe("later.csv");
		dispatch({ src: "/blobs/x" });
		expect(slot("file-link")?.getAttribute("href")).toBe("/blobs/x");
	});

	it("says there is no file with neither source nor name", () => {
		mount("FileRef", {});
		expect(slot("file-name")?.textContent).toBe("No file");
	});

	it("picks a glyph and a label by mime", () => {
		expect(fileGlyph("image/png").displayName).toContain("Image");
		expect(fileGlyph("text/csv").displayName).toContain("Spreadsheet");
		expect(fileGlyph("application/zip").displayName).toContain("Archive");
		expect(fileGlyph("").displayName).toBe(fileGlyph("application/x-thing").displayName);
		expect(fileType("application/pdf")).toBe("PDF");
		expect(fileType("image/svg+xml")).toBe("XML");
		expect(fileType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")).toBe(
			"SHEET",
		);
		expect(fileType("")).toBe("");
		expect(fileName("/a/b/")).toBe("");
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

describe("MediaVolume", () => {
	/** A transport with no element: volume and mute you can watch. */
	function Harness({ onMenu }: { onMenu?: (open: boolean) => void }) {
		const [s, setS] = useState<MediaSnapshot>({ ...EMPTY_SNAPSHOT, ready: true, duration: 60 });
		const set = (patch: Partial<MediaSnapshot>) => setS((p) => ({ ...p, ...patch }));
		const media: MediaApi = {
			...s,
			ref: () => {},
			el: null,
			play: () => {},
			pause: () => {},
			toggle: () => {},
			seek: () => {},
			seekBy: () => {},
			seekFraction: () => {},
			setVolume: (v) => set({ volume: v, muted: v <= 0 }),
			setMuted: (muted) => set({ muted }),
			toggleMute: () => set({ muted: !s.muted }),
			setRate: () => {},
		};
		return <MediaControls media={media} onMenuOpenChange={onMenu} />;
	}

	const box = () => slot("media-volume") as HTMLElement;
	const mute = () => box().querySelector("button") as HTMLButtonElement;
	const panel = () => slot("media-volume-panel");
	const thumb = () => panel()?.querySelector<HTMLElement>("[role=slider]") ?? null;
	const fire = (el: Element, type: string, init: PointerEventInit = {}) =>
		act(() => {
			el.dispatchEvent(new PointerEvent(type, { bubbles: true, pointerType: "mouse", ...init }));
		});
	const key = (el: Element, k: string) =>
		act(() => {
			el.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
		});
	const wait = (ms: number) =>
		act(async () => {
			await new Promise((r) => setTimeout(r, ms));
		});

	it("is shut at rest, with nothing beside the button to grow", () => {
		act(() => root.render(<Harness />));
		expect(panel()).toBeNull();
		expect(box().children).toHaveLength(1);
		expect(mute().getAttribute("aria-label")).toBe("Mute");
	});

	it("floats a vertical level over the button on hover and keeps the bar up", async () => {
		const menu = vi.fn();
		act(() => root.render(<Harness onMenu={menu} />));
		fire(mute(), "pointerover");
		expect(panel()).not.toBeNull();
		// Portalled into its own box: right after the button in tab order.
		expect(box().contains(panel())).toBe(true);
		expect(panel()?.getAttribute("data-side")).toBe("top");
		expect(thumb()?.getAttribute("aria-orientation")).toBe("vertical");
		expect(thumb()?.getAttribute("aria-valuetext")).toBe("100%");
		expect(slot("media-volume-level")?.textContent).toBe("100%");
		expect(menu).toHaveBeenLastCalledWith(true);

		// A click still mutes, and the panel stays.
		act(() => mute().click());
		expect(mute().getAttribute("aria-label")).toBe("Unmute");
		expect(slot("media-volume-level")?.textContent).toBe("0%");
		expect(panel()).not.toBeNull();

		// Leaving waits a moment, so the pointer can cross into the panel.
		fire(mute(), "pointerout", { relatedTarget: document.body });
		expect(panel()).not.toBeNull();
		fire(panel() as Element, "pointerover", { relatedTarget: document.body });
		await wait(200);
		expect(panel()).not.toBeNull();
		fire(panel() as Element, "pointerout", { relatedTarget: document.body });
		await wait(200);
		expect(panel()).toBeNull();
		expect(menu).toHaveBeenLastCalledWith(false);
	});

	it("opens on keyboard focus, steps on the arrows, shuts on Escape", async () => {
		act(() => root.render(<Harness />));
		act(() => mute().focus());
		expect(panel()).not.toBeNull();
		const t = thumb() as HTMLElement;
		act(() => t.focus());
		key(t, "ArrowDown");
		expect(slot("media-volume-level")?.textContent).toBe("95%");
		key(t, "Escape");
		await wait(0);
		expect(panel()).toBeNull();
		expect(document.activeElement).toBe(mute());
		// Back on the button, still shut until focus leaves and comes back.
		act(() => mute().blur());
		act(() => mute().focus());
		expect(panel()).not.toBeNull();
	});

	it("is the mute button alone in touch mode: no panel on hover or focus", () => {
		act(() =>
			root.render(
				<TouchProvider value>
					<Harness />
				</TouchProvider>,
			),
		);
		fire(mute(), "pointerover", { pointerType: "touch" });
		act(() => mute().focus());
		expect(panel()).toBeNull();
		act(() => mute().click());
		expect(mute().getAttribute("aria-label")).toBe("Unmute");
		expect(panel()).toBeNull();
	});

	it("does not hold the panel up for a focus a click gave", async () => {
		act(() => root.render(<Harness />));
		fire(mute(), "pointerover");
		fire(mute(), "pointerdown");
		act(() => mute().focus());
		fire(mute(), "pointerup");
		fire(mute(), "pointerout", { relatedTarget: document.body });
		await wait(200);
		expect(panel()).toBeNull();
	});
});
