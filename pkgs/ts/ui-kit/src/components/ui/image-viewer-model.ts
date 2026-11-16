// The image viewer's geometry: fit, zoom toward a point, pan and its clamp.
// React-free, so the component and the tests share it.
//
// A view is the image drawn at `scale` image pixels per screen pixel, its top
// left corner at (x, y) in the box. Every move goes through `clampView`, which
// holds two rules: the scale stays inside the limits, and the image cannot be
// lost. A side that fits in the box sits centred on that axis; a side larger
// than the box covers it edge to edge, so dragging stops at the image's edge.

export type Size = { w: number; h: number };
export type Point = { x: number; y: number };
export type View = { scale: number; x: number; y: number };

/** The deepest zoom, unless a tiny image needs more room past its fit. */
export const MAX_SCALE = 32;

/** Where the zoom buttons and keys stop. Fit is not on it; it has its own button. */
export const ZOOM_STEPS: readonly number[] = [
	0.05, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 32,
];

const EPS = 1e-3;

/** Whether two scales are the same to the eye. */
export function sameScale(a: number, b: number): boolean {
	return Math.abs(a - b) <= EPS * Math.max(1, b);
}

function empty(s: Size): boolean {
	return !(s.w > 0 && s.h > 0);
}

/** The scale that shows the whole image in the box, up or down. 1 while either has no size. */
export function fitScale(img: Size, box: Size): number {
	if (empty(img) || empty(box)) return 1;
	return Math.min(box.w / img.w, box.h / img.h);
}

/** Zoom limits: out to fit or 1:1, whichever is smaller; in to MAX_SCALE, or four fits for a tiny image. */
export function scaleLimits(img: Size, box: Size): { min: number; max: number } {
	const fit = fitScale(img, box);
	return { min: Math.min(fit, 1), max: Math.max(MAX_SCALE, fit * 4) };
}

function clampAxis(at: number, length: number, room: number): number {
	if (length <= room) return (room - length) / 2;
	return Math.min(0, Math.max(room - length, at));
}

/** The view held inside the limits and the box. */
export function clampView(view: View, img: Size, box: Size): View {
	const { min, max } = scaleLimits(img, box);
	const scale = Math.min(max, Math.max(min, view.scale));
	return {
		scale,
		x: clampAxis(view.x, img.w * scale, box.w),
		y: clampAxis(view.y, img.h * scale, box.h),
	};
}

/** The whole image, centred. */
export function fitView(img: Size, box: Size): View {
	return clampView({ scale: fitScale(img, box), x: 0, y: 0 }, img, box);
}

/** Zoom to `scale` keeping the image pixel under `at` (a box point) where it is. */
export function zoomAt(view: View, scale: number, at: Point, img: Size, box: Size): View {
	const { min, max } = scaleLimits(img, box);
	const next = Math.min(max, Math.max(min, scale));
	const k = next / view.scale;
	return clampView(
		{ scale: next, x: at.x - (at.x - view.x) * k, y: at.y - (at.y - view.y) * k },
		img,
		box,
	);
}

/** The box's centre, where the buttons and keys zoom toward. */
export function centre(box: Size): Point {
	return { x: box.w / 2, y: box.h / 2 };
}

/** The next step on the ladder in `dir` (+1 in, -1 out), held to the limits. */
export function stepScale(
	scale: number,
	dir: 1 | -1,
	limits: { min: number; max: number },
): number {
	const next =
		dir > 0
			? (ZOOM_STEPS.find((s) => s > scale * (1 + EPS)) ?? limits.max)
			: ([...ZOOM_STEPS].reverse().find((s) => s < scale * (1 - EPS)) ?? limits.min);
	return Math.min(limits.max, Math.max(limits.min, next));
}

/**
 * The scale after one wheel event. A mouse notch (about 100px, or 3 lines)
 * moves about a fifth; a trackpad pinch arrives as ctrl+wheel in small deltas
 * and gets a finer, faster rate so it tracks the fingers.
 */
export function wheelScale(
	scale: number,
	deltaY: number,
	deltaMode: number,
	pinch: boolean,
): number {
	const px = deltaMode === 1 ? deltaY * 16 : deltaMode === 2 ? deltaY * 400 : deltaY;
	const rate = pinch ? 0.01 : 0.002;
	// Cap one event so a fast flick cannot leap the whole range.
	const step = Math.max(-0.5, Math.min(0.5, -px * rate));
	return scale * Math.exp(step);
}

/** Pan by a screen distance. */
export function panBy(view: View, dx: number, dy: number, img: Size, box: Size): View {
	return clampView({ ...view, x: view.x + dx, y: view.y + dy }, img, box);
}

/** Whether the image is larger than the box on either axis, so a drag moves it. */
export function canPan(view: View, img: Size, box: Size): boolean {
	return img.w * view.scale > box.w + 0.5 || img.h * view.scale > box.h + 0.5;
}

/**
 * The double click: from fit, in to the point (1:1 for a large image, twice
 * the fit for a small one, so a 28px sample still gets closer); from anywhere
 * else, back to fit.
 */
export function toggleView(view: View, at: Point, img: Size, box: Size): View {
	const fit = fitScale(img, box);
	if (!sameScale(view.scale, fit)) return fitView(img, box);
	return zoomAt(view, fit < 1 ? 1 : fit * 2, at, img, box);
}

/** The image pixel under a box point, or null off the image. */
export function pixelAt(view: View, at: Point, img: Size): Point | null {
	const x = Math.floor((at.x - view.x) / view.scale);
	const y = Math.floor((at.y - view.y) / view.scale);
	if (x < 0 || y < 0 || x >= img.w || y >= img.h) return null;
	return { x, y };
}

/** The zoom as the readout says it: a whole percent. */
export function zoomLabel(scale: number): string {
	return `${Math.round(scale * 100)}%`;
}
