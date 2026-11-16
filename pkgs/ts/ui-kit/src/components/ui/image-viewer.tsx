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
//   arrows       pan, while zoomed (shift for a longer step)
//
// Until the reader zooms, the view follows the box: a resize refits. Past 1:1
// the image draws with hard pixels, so a small or ML image stays crisp. The
// controls cluster in the corner rests hidden and shows on hover or focus
// (`controls="always"` pins it, `"none"` drops it); on a touch screen it is
// always shown. `expandable` adds a button that opens the same viewer over
// the whole window, Esc to close (`expanded` holds it from outside). `pixel` shows the image pixel under the
// pointer.
//
// The box has no size of its own: give it a height, or an `aspectRatio` with
// a width. With neither it is 320px tall (h-80).

import { Maximize2, Scan, ZoomIn, ZoomOut } from "lucide-react";
import * as React from "react";
import { useKeyScope } from "../../lib/keyboard";
import { cn } from "../../lib/utils";
import { Dialog, DialogContent, DialogTitle } from "./dialog";
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
	/** The full-window view, held by the caller; uncontrolled unless set. */
	expanded?: boolean;
	onExpandedChange?: (open: boolean) => void;
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
	expanded: expandedProp,
	onExpandedChange,
	className,
	style,
	...props
}: ImageViewerProps) {
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

	const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
		if (e.button !== 0 || !pannable) return;
		e.currentTarget.setPointerCapture(e.pointerId);
		drag.current = { id: e.pointerId, x: e.clientX, y: e.clientY };
		setDragging(true);
	};
	const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
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
		if (drag.current?.id !== e.pointerId) return;
		drag.current = null;
		setDragging(false);
	};

	const onDoubleClick = (e: React.MouseEvent<HTMLDivElement>) => {
		if (!ready) return;
		const next = toggleView(view, pointIn(e.currentTarget, e), size, box);
		show(next, true);
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
				)}
				{...keys}
				onPointerDown={onPointerDown}
				onPointerMove={onPointerMove}
				onPointerUp={endDrag}
				onPointerCancel={endDrag}
				onPointerLeave={() => setHover(null)}
				onDoubleClick={onDoubleClick}
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
						"pointer-events-none absolute bottom-2 left-2 rounded-sm px-1.5 py-0.5",
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
							"absolute right-2 bottom-2 flex items-center gap-0.5 rounded-md p-0.5",
							"border border-border-subtle bg-bg-elevated shadow-raised",
							"transition-opacity duration-fast ease-out",
							controls === "hover" &&
								"opacity-0 group-hover/viewer:opacity-100 group-focus-within/viewer:opacity-100 [@media(hover:none)]:opacity-100",
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
							<Scan />
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
						{expandable && (
							<>
								<span aria-hidden="true" className="mx-0.5 h-4 w-px bg-border-subtle" />
								<Control label="Expand" onClick={() => setExpanded(true)}>
									<Maximize2 />
								</Control>
							</>
						)}
					</div>
				</TooltipProvider>
			)}

			{(expandable || expandedProp !== undefined) && (
				<Dialog open={expanded} onOpenChange={setExpanded}>
					<DialogContent
						data-slot="image-viewer-overlay"
						aria-describedby={undefined}
						className={cn(
							"top-0 left-0 block h-dvh w-dvw max-w-none translate-x-0 translate-y-0",
							"rounded-none border-0 bg-bg-canvas p-0",
						)}
					>
						<DialogTitle className="sr-only">{alt || "Image"}</DialogTitle>
						<ImageViewer
							src={src}
							alt={alt}
							controls="always"
							expandable={false}
							pixel={pixel}
							className="h-full bg-bg-canvas"
						/>
					</DialogContent>
				</Dialog>
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
