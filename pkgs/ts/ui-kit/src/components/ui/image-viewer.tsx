// ImageViewer primitive: an image you can zoom into and move around.
//
// The plain Image stays a thin <img>; this one is its own box with the image
// placed inside it. The geometry (fit, zoom toward a point, the pan clamp)
// lives in ./image-viewer-model.ts; this file is the input and the drawing.
//
//   wheel        zoom toward the pointer (ctrl+wheel, a trackpad pinch, finer)
//   drag         pan, while the image is larger than the box
//   double click fit -> zoom in at the point; anywhere else -> fit
//   + / -        zoom in / out a step, toward the centre
//   0 / 1        fit / 1:1
//   f            full window, and back
//   arrows       pan, while zoomed (shift for a longer step)
//
// In touch mode (../../lib/touch.ts) the hand does the same: two fingers
// pinch toward their midpoint and move the image as they go, one finger pans
// while zoomed, a double tap toggles fit. At fit a one finger swipe still
// scrolls the page, so a viewer in a long page does not trap it.
//
// Until the reader zooms, the view follows the box: a resize refits. Past 1:1
// the image draws with hard pixels, so a small or ML image stays crisp. The
// controls cluster in the corner rests hidden and shows on hover or focus
// (`controls="always"` pins it, `"none"` drops it); in touch mode, where
// nothing hovers, it is always shown. `expandable` adds a button that opens
// the same viewer over the whole window, Esc to close (`expanded` holds it
// from outside). It is the video player's full screen button, and in the full
// window view the exit button takes its place in the cluster, so the way out
// is where the way in was; a solid close button sits top right too, both
// clear of the notch and the home indicator. `download` adds a download link
// to the cluster, in both views. `pixel` shows the image pixel under the
// pointer.
//
// The full window view is the viewer's own full screen, not a dialog: it is
// built on the Radix dialog primitive directly, so it stays the whole window
// in touch mode, where a kit Dialog becomes a bottom sheet.
//
// The box has no size of its own: give it a height, or an `aspectRatio` with
// a width. With neither it is 320px tall (h-80).

import { Download, Maximize, Minimize, RotateCcw, X, ZoomIn, ZoomOut } from "lucide-react";
import { Dialog as DialogPrimitive } from "radix-ui";
import * as React from "react";
import { useKeyScope } from "../../lib/keyboard";
import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";
import { RADIUS_CLASS } from "./image";
import {
	canPan,
	centre,
	clampView,
	fitScale,
	fitView,
	type Point,
	panBy,
	pixelAt,
	type Size,
	sameScale,
	scaleLimits,
	stepScale,
	toggleView,
	type View,
	wheelScale,
	zoomAt,
	zoomLabel,
} from "./image-viewer-model";
import { Shortcut } from "./shortcut";
import { TooltipProvider } from "./tooltip";

const PAN_STEP = 48;
/** A second tap within this long, and this close, is a double tap. */
const DOUBLE_TAP_MS = 300;
const DOUBLE_TAP_PX = 24;
/** A touch that moved further than this was a swipe, not a tap. */
const TAP_SLOP_PX = 10;
// The full window view's corners: 20px in, plus the notch and home
// indicator's safe area on a phone (zero elsewhere).
const EDGE_BL =
	"bottom-[calc(1.25rem+env(safe-area-inset-bottom))] left-[calc(1.25rem+env(safe-area-inset-left))]";
const EDGE_BR =
	"right-[calc(1.25rem+env(safe-area-inset-right))] bottom-[calc(1.25rem+env(safe-area-inset-bottom))]";

export interface ImageViewerProps extends Omit<React.ComponentProps<"div">, "children"> {
	src?: string;
	alt: string;
	radius?: keyof typeof RADIUS_CLASS;
	/** A CSS aspect ratio ("16 / 9") for the box; the width comes from the container. */
	aspectRatio?: string;
	/** The zoom cluster: shown on hover and focus, always, or not at all. */
	controls?: "hover" | "always" | "none";
	/** A button that opens the viewer over the whole window. */
	expandable?: boolean;
	/** Show the image pixel under the pointer. */
	pixel?: boolean;
	/** A url that saves the image: a download link in the cluster. */
	download?: string;
	/** The full-window view, held by the caller; uncontrolled unless set. */
	expanded?: boolean;
	onExpandedChange?: (open: boolean) => void;
	/** Draws the exit button where expand sits, and the full window insets. Internal. */
	onExit?: () => void;
}

type State = { view: View; follow: boolean; smooth: boolean };

const FOLLOW: State = { view: { scale: 1, x: 0, y: 0 }, follow: true, smooth: false };

// The layout size, not the drawn one: a box inside an opening dialog is
// scaled for a moment, and a border is not room for the image.
function useBoxSize(ref: React.RefObject<HTMLElement | null>): Size {
	const [size, setSize] = React.useState<Size>({ w: 0, h: 0 });
	React.useLayoutEffect(() => {
		const el = ref.current;
		if (!el) return;
		const measure = () => {
			const w = el.clientWidth;
			const h = el.clientHeight;
			setSize((s) => (s.w === w && s.h === h ? s : { w, h }));
		};
		measure();
		if (typeof ResizeObserver === "undefined") return;
		const ro = new ResizeObserver(measure);
		ro.observe(el);
		return () => ro.disconnect();
	}, [ref]);
	return size;
}

function ImageViewer({
	src,
	alt,
	radius = "none",
	aspectRatio,
	controls = "hover",
	expandable = true,
	pixel = false,
	download,
	expanded: expandedProp,
	onExpandedChange,
	onExit,
	className,
	style,
	...props
}: ImageViewerProps) {
	const touch = useTouch();
	const stageRef = React.useRef<HTMLDivElement>(null);
	const box = useBoxSize(stageRef);
	const [img, setImg] = React.useState<Size | null>(null);
	const [state, setState] = React.useState<State>(FOLLOW);
	const [dragging, setDragging] = React.useState(false);
	const [hover, setHover] = React.useState<Point | null>(null);
	const [expandedOwn, setExpandedOwn] = React.useState(false);
	const expanded = expandedProp ?? expandedOwn;
	const setExpanded = (open: boolean) => {
		setExpandedOwn(open);
		onExpandedChange?.(open);
	};
	const drag = React.useRef<{ id: number; x: number; y: number } | null>(null);
	// Touch: the fingers down, where each one started, the pinch in progress
	// (its start: finger distance, midpoint in the box, the view then), and
	// the last tap, for the double tap.
	const fingers = React.useRef(new Map<number, Point & { x0: number; y0: number }>());
	const pinch = React.useRef<{ dist: number; mid: Point; view: View } | null>(null);
	const pinched = React.useRef(false);
	const lastTap = React.useRef<{ t: number; x: number; y: number } | null>(null);

	// A new source starts over: unknown size, following the box. Done during
	// render, so a cached image's load cannot land before the reset.
	const [shownSrc, setShownSrc] = React.useState(src);
	if (shownSrc !== src) {
		setShownSrc(src);
		setImg(null);
		setState(FOLLOW);
		setHover(null);
	}

	const size = img ?? { w: 0, h: 0 };
	const ready = img !== null && box.w > 0 && box.h > 0;
	// The view as drawn: the fit while following, otherwise the last view held
	// to the box as it is now.
	const view = state.follow ? fitView(size, box) : clampView(state.view, size, box);
	const limits = scaleLimits(size, box);
	const fit = fitScale(size, box);
	const pannable = ready && canPan(view, size, box);

	// Handlers outside React's render (the wheel listener) read these.
	const live = React.useRef({ view, size, box, ready });
	live.current = { view, size, box, ready };

	const show = React.useCallback((next: View, smooth: boolean) => {
		const { size: s, box: b } = live.current;
		setState({ view: next, follow: sameScale(next.scale, fitScale(s, b)), smooth });
	}, []);

	const zoomStep = (dir: 1 | -1) =>
		show(zoomAt(view, stepScale(view.scale, dir, limits), centre(box), size, box), true);
	const toFit = () => setState({ view: fitView(size, box), follow: true, smooth: true });
	const toActual = () => show(zoomAt(view, 1, centre(box), size, box), true);
	const pan = (dx: number, dy: number) => show(panBy(view, dx, dy, size, box), true);

	const step = (e: React.KeyboardEvent) => (e.shiftKey ? PAN_STEP * 4 : PAN_STEP);
	const keys = useKeyScope<HTMLDivElement>({
		"+": () => zoomStep(1),
		"=": () => zoomStep(1),
		"-": () => zoomStep(-1),
		_: () => zoomStep(-1),
		"0": toFit,
		"1": toActual,
		...(onExit ? { f: onExit } : expandable ? { f: () => setExpanded(true) } : {}),
		// Arrows only while there is somewhere to go, so otherwise they scroll the page.
		...(pannable
			? {
					ArrowLeft: (e) => pan(step(e), 0),
					ArrowRight: (e) => pan(-step(e), 0),
					ArrowUp: (e) => pan(0, step(e)),
					ArrowDown: (e) => pan(0, -step(e)),
				}
			: {}),
	});

	// Wheel needs a non-passive listener to keep the page from scrolling.
	React.useEffect(() => {
		const el = stageRef.current;
		if (!el) return;
		const onWheel = (e: WheelEvent) => {
			const { view: v, size: s, box: b, ready: r } = live.current;
			if (!r) return;
			e.preventDefault();
			const at = pointIn(el, e);
			show(zoomAt(v, wheelScale(v.scale, e.deltaY, e.deltaMode, e.ctrlKey), at, s, b), false);
		};
		el.addEventListener("wheel", onWheel, { passive: false });
		return () => el.removeEventListener("wheel", onWheel);
	}, [show]);

	// The two fingers' distance and midpoint (in the box), for the pinch.
	const span = (el: Element) => {
		const [a, b] = [...fingers.current.values()];
		return {
			dist: Math.hypot(a.x - b.x, a.y - b.y),
			mid: pointIn(el, { clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2 }),
		};
	};

	const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
		if (e.button !== 0) return;
		if (e.pointerType === "touch") {
			const at = { x: e.clientX, y: e.clientY };
			fingers.current.set(e.pointerId, { ...at, x0: at.x, y0: at.y });
			if (fingers.current.size === 1) pinched.current = false;
			if (fingers.current.size === 2 && ready) {
				// The second finger turns a pan into a pinch, from wherever the
				// image is now.
				const { dist, mid } = span(e.currentTarget);
				pinch.current = { dist: Math.max(1, dist), mid, view };
				pinched.current = true;
				drag.current = null;
				setDragging(false);
				return;
			}
			if (fingers.current.size > 2) return;
		}
		if (!pannable) return;
		e.currentTarget.setPointerCapture(e.pointerId);
		drag.current = { id: e.pointerId, x: e.clientX, y: e.clientY };
		setDragging(true);
	};
	const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
		const finger = fingers.current.get(e.pointerId);
		if (finger) {
			finger.x = e.clientX;
			finger.y = e.clientY;
			const p = pinch.current;
			if (p && fingers.current.size >= 2) {
				const { dist, mid } = span(e.currentTarget);
				const zoomed = zoomAt(p.view, (p.view.scale * dist) / p.dist, p.mid, size, box);
				show(panBy(zoomed, mid.x - p.mid.x, mid.y - p.mid.y, size, box), false);
				return;
			}
		}
		const d = drag.current;
		if (d && d.id === e.pointerId) {
			const dx = e.clientX - d.x;
			const dy = e.clientY - d.y;
			drag.current = { ...d, x: e.clientX, y: e.clientY };
			show(panBy(view, dx, dy, size, box), false);
		}
		if (pixel && ready) setHover(pixelAt(view, pointIn(e.currentTarget, e), size));
	};
	const endDrag = (e: React.PointerEvent<HTMLDivElement>) => {
		const finger = fingers.current.get(e.pointerId);
		if (finger) {
			fingers.current.delete(e.pointerId);
			if (pinch.current && fingers.current.size < 2) {
				pinch.current = null;
				// The finger left on the glass carries on as a pan, from here.
				const [rest] = [...fingers.current.entries()];
				const { view: v, size: s, box: b } = live.current;
				if (rest && canPan(v, s, b)) {
					drag.current = { id: rest[0], x: rest[1].x, y: rest[1].y };
					setDragging(true);
				}
			}
			if (e.type === "pointerup" && fingers.current.size === 0 && !pinched.current) {
				const moved = Math.hypot(e.clientX - finger.x0, e.clientY - finger.y0);
				if (moved <= TAP_SLOP_PX) tapped(e);
			}
		}
		if (drag.current?.id !== e.pointerId) return;
		drag.current = null;
		setDragging(false);
	};

	const toggleAt = (at: Point) => {
		if (!ready) return;
		show(toggleView(view, at, size, box), true);
	};
	const onDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
		toggleAt(pointIn(e.currentTarget, e));
	};
	// A double tap is the double click. Counted here rather than left to the
	// browser, which does not send a dblclick for a double tap everywhere.
	const tapped = (e: React.PointerEvent<HTMLDivElement>) => {
		const last = lastTap.current;
		const now = e.timeStamp;
		if (
			last &&
			now - last.t <= DOUBLE_TAP_MS &&
			Math.hypot(e.clientX - last.x, e.clientY - last.y) <= DOUBLE_TAP_PX
		) {
			lastTap.current = null;
			toggleAt(pointIn(e.currentTarget, e));
			return;
		}
		lastTap.current = { t: now, x: e.clientX, y: e.clientY };
	};

	const onLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
		const el = e.currentTarget;
		// An svg with no size of its own reports 0: give it the box.
		const { w, h } = live.current.box;
		setImg(
			el.naturalWidth > 0 && el.naturalHeight > 0
				? { w: el.naturalWidth, h: el.naturalHeight }
				: { w: w || 300, h: h || 150 },
		);
	};

	const scale = view.scale;
	const crisp = ready && scale > 1 && !sameScale(scale, 1);

	return (
		<div
			data-slot="image-viewer"
			className={cn(
				"group/viewer relative w-full overflow-hidden bg-bg-sunken",
				RADIUS_CLASS[radius],
				!aspectRatio && "h-80",
				className,
			)}
			style={{ aspectRatio, ...style }}
			{...props}
		>
			{/* biome-ignore lint/a11y/useSemanticElements: a focusable surface that owns its keys, not a form section */}
			<div
				ref={stageRef}
				data-slot="image-viewer-stage"
				role="group"
				aria-roledescription="image viewer"
				aria-label={alt || "Image"}
				aria-keyshortcuts="+ - 0 1"
				className={cn(
					"absolute inset-0 select-none outline-hidden",
					"focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
					"rounded-[inherit]",
					pannable ? (dragging ? "cursor-grabbing" : "cursor-grab") : "cursor-default",
					pannable && "touch-none",
					// At fit the page keeps its one finger scroll, the pinch is ours.
					touch && !pannable && "touch-pan-x touch-pan-y",
				)}
				{...keys}
				onPointerDown={onPointerDown}
				onPointerMove={onPointerMove}
				onPointerUp={endDrag}
				onPointerCancel={endDrag}
				onPointerLeave={() => setHover(null)}
				onDoubleClick={touch ? undefined : onDoubleClick}
			>
				{src ? (
					<img
						key={src}
						src={src}
						alt={alt}
						loading="lazy"
						decoding="async"
						draggable={false}
						onLoad={onLoad}
						className={cn(
							"pointer-events-none absolute top-0 left-0 max-w-none",
							!ready && "invisible",
							state.smooth &&
								"transition-[width,height,transform] duration-fast ease-out motion-reduce:transition-none",
						)}
						style={
							ready
								? {
										width: size.w * scale,
										height: size.h * scale,
										transform: `translate(${view.x}px, ${view.y}px)`,
										imageRendering: crisp ? "pixelated" : undefined,
									}
								: undefined
						}
					/>
				) : null}
			</div>

			{pixel && hover && (
				<div
					data-slot="image-viewer-pixel"
					aria-hidden="true"
					className={cn(
						"pointer-events-none absolute rounded-sm px-1.5 py-0.5",
						onExit ? EDGE_BL : "bottom-2 left-2",
						"border border-border-subtle bg-bg-elevated shadow-raised",
						"font-mono text-xs tabular-nums text-text-secondary",
					)}
				>
					{hover.x}, {hover.y}
				</div>
			)}

			{ready && controls !== "none" && (
				<TooltipProvider>
					{/* biome-ignore lint/a11y/useSemanticElements: a cluster of buttons, not a form section with a legend */}
					<div
						data-slot="image-viewer-controls"
						role="group"
						aria-label="Zoom"
						className={cn(
							"absolute flex items-center gap-0.5 rounded-md p-0.5",
							onExit ? EDGE_BR : "right-2 bottom-2",
							"border border-border-subtle bg-bg-elevated shadow-raised",
							"transition-opacity duration-fast ease-out",
							controls === "hover" &&
								!touch &&
								"opacity-0 group-hover/viewer:opacity-100 group-focus-within/viewer:opacity-100",
						)}
					>
						<Control
							label="Zoom out"
							keys={["-"]}
							off={scale <= limits.min * 1.001}
							onClick={() => zoomStep(-1)}
						>
							<ZoomOut />
						</Control>
						<span
							data-slot="image-viewer-zoom"
							className="min-w-10 px-0.5 text-center font-mono text-xs tabular-nums text-text-secondary"
						>
							{zoomLabel(scale)}
						</span>
						<Control
							label="Zoom in"
							keys={["+"]}
							off={scale >= limits.max * 0.999}
							onClick={() => zoomStep(1)}
						>
							<ZoomIn />
						</Control>
						<span aria-hidden="true" className="mx-0.5 h-4 w-px bg-border-subtle" />
						<Control label="Fit" keys={["0"]} off={sameScale(scale, fit)} onClick={toFit}>
							<RotateCcw />
						</Control>
						<Control
							label="Actual size"
							keys={["1"]}
							off={sameScale(scale, 1)}
							onClick={toActual}
							className="w-auto px-1 font-mono text-[11px] font-medium"
						>
							1:1
						</Control>
						{download && (
							<>
								<span aria-hidden="true" className="mx-0.5 h-4 w-px bg-border-subtle" />
								<IconButton
									asChild
									variant="ghost"
									size="sm"
									ring="inset"
									aria-label="Download"
									tip="Download"
									tipSide="top"
									data-slot="image-viewer-download"
								>
									<a href={download} download>
										<Download />
									</a>
								</IconButton>
							</>
						)}
						{(expandable || onExit) && (
							<>
								<span aria-hidden="true" className="mx-0.5 h-4 w-px bg-border-subtle" />
								{onExit ? (
									<Control label="Exit full screen" keys={["F"]} onClick={onExit}>
										<Minimize />
									</Control>
								) : (
									<Control label="Full screen" keys={["F"]} onClick={() => setExpanded(true)}>
										<Maximize />
									</Control>
								)}
							</>
						)}
					</div>
				</TooltipProvider>
			)}

			{(expandable || expandedProp !== undefined) && (
				<DialogPrimitive.Root open={expanded} onOpenChange={setExpanded}>
					<DialogPrimitive.Portal>
						<DialogPrimitive.Content
							data-slot="image-viewer-overlay"
							aria-describedby={undefined}
							className={cn(
								"fixed inset-0 z-50 block h-dvh w-dvw bg-bg-canvas outline-hidden",
								// The dialog's motion (motion.md §3 Dialog), without the scale.
								"data-[state=open]:animate-in data-[state=closed]:animate-out",
								"data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
								"data-[state=open]:duration-slow data-[state=closed]:duration-slow",
								"data-[state=open]:ease-out data-[state=closed]:ease-in",
							)}
						>
							<DialogPrimitive.Title className="sr-only">{alt || "Image"}</DialogPrimitive.Title>
							<ImageViewer
								src={src}
								alt={alt}
								controls="always"
								expandable={false}
								pixel={pixel}
								download={download}
								onExit={() => setExpanded(false)}
								className="h-full bg-bg-canvas"
							/>
							{/* Solid, not ghost: it sits on the image once zoomed in. */}
							<DialogPrimitive.Close asChild>
								<IconButton
									data-slot="image-viewer-close"
									variant="secondary"
									size="md"
									aria-label="Close"
									className={cn(
										"absolute shadow-raised",
										"top-[calc(1.25rem+env(safe-area-inset-top))] right-[calc(1.25rem+env(safe-area-inset-right))]",
									)}
								>
									<X />
								</IconButton>
							</DialogPrimitive.Close>
						</DialogPrimitive.Content>
					</DialogPrimitive.Portal>
				</DialogPrimitive.Root>
			)}
		</div>
	);
}

/** A cluster button. `off` is shown and announced as unavailable but keeps focus. */
function Control({
	label,
	keys,
	off = false,
	onClick,
	className,
	children,
}: {
	label: string;
	keys?: string[];
	off?: boolean;
	onClick: () => void;
	className?: string;
	children: React.ReactNode;
}) {
	return (
		<IconButton
			variant="ghost"
			size="sm"
			ring="inset"
			aria-label={label}
			aria-disabled={off || undefined}
			tip={
				<span className="flex items-center gap-2">
					{label}
					{keys && <Shortcut keys={keys} size="sm" />}
				</span>
			}
			tipSide="top"
			// Not `disabled`: the button that was just used often goes unavailable
			// (Fit after fitting), and a real disabled would drop the focus.
			onClick={off ? undefined : onClick}
			className={cn("aria-disabled:opacity-50 aria-disabled:hover:bg-transparent", className)}
		>
			{children}
		</IconButton>
	);
}

function pointIn(el: Element, e: { clientX: number; clientY: number }): Point {
	const r = el.getBoundingClientRect();
	return { x: e.clientX - r.left, y: e.clientY - r.top };
}

export { ImageViewer };
