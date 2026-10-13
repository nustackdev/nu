import {
	ArrowUpRight,
	ChevronDown,
	Circle,
	type LucideIcon,
	Pencil,
	Redo2,
	Slash,
	Square,
	Trash2,
	Undo2,
} from "lucide-react";
import * as React from "react";

import { cn } from "../../lib/utils";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuShortcut,
	DropdownMenuTrigger,
} from "./dropdown-menu";
import { IconButton } from "./icon-button";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { Separator } from "./separator";
import { Shortcut } from "./shortcut";
import {
	arrowPath,
	freehandPath,
	normalizeElements,
	SKETCH_FILLS,
	SKETCH_SHAPES,
	SKETCH_SIZES,
	SKETCH_STROKES,
	type SketchControl,
	type SketchDefaults,
	type SketchElement,
	type SketchPoint,
	type SketchShape,
	type SketchTool,
	sketchColor,
	sketchConfig,
} from "./sketch-board-model";
import { toggleVariants } from "./toggle";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

// A board a person draws on with a pointer: mouse, pen or touch. Human input
// first, and a surface a program can draw on by writing elements. Pen ink is
// perfect-freehand, pressure-aware from a pen and simulated from speed
// otherwise; shapes are rect, ellipse, line and arrow. No Radix equivalent,
// and deliberately not a canvas library: SVG over the board's own pixel box,
// so ink is crisp at any pixel ratio and every color is a kit role that
// restains with the theme.
//
// The value is a list of elements (see ./sketch-board-model). An element in
// flight lives in a ref and only the draft layer re-renders per move;
// `onValueChange` fires once per committed element, once per undo or redo
// and once on clear, never per pointer move.
//
// Config is what a program sets: which `tools` exist, which toolbar
// `controls` show (none at all is no toolbar), the starting tool, colors and
// size in `defaults`. What the person picks in the toolbar is local state and
// never on the wire. Undo and redo walk this board's own commits; a value
// from outside (a server write) starts the history over.
//
// Keys, with the board focused: P pen, R rect, O ellipse, L line, A arrow,
// mod+Z undo, mod+shift+Z or mod+Y redo, Esc drops the element in flight.

export interface SketchBoardProps
	extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange" | "defaultValue"> {
	/** The elements. Anything off-shape is skipped, never thrown on. */
	value: readonly unknown[];
	onValueChange?: (value: SketchElement[]) => void;
	/** Board width in px. It never grows past its container. */
	width?: number;
	/** Board height in px; the width when unset. The aspect ratio holds as it shrinks. */
	height?: number;
	tools?: readonly SketchTool[];
	/** Toolbar items, in toolbar order of the kit. Empty is no toolbar. */
	controls?: readonly SketchControl[];
	defaults?: Partial<SketchDefaults>;
	/** Draws the value and takes no input. */
	readonly?: boolean;
	/** Accessible name of the board. */
	label?: string;
}

const MIN_STEP = 0.002;
const MIN_SHAPE = 0.008;
const HISTORY = 200;
const round = (n: number) => Math.round(n * 10000) / 10000;
const clamp01 = (n: number) => (n < 0 ? 0 : n > 1 ? 1 : n);

const TOOL_META: Record<SketchTool, { label: string; key: string; icon: LucideIcon }> = {
	pen: { label: "Pen", key: "P", icon: Pencil },
	rect: { label: "Rectangle", key: "R", icon: Square },
	ellipse: { label: "Ellipse", key: "O", icon: Circle },
	line: { label: "Line", key: "L", icon: Slash },
	arrow: { label: "Arrow", key: "A", icon: ArrowUpRight },
};
const KEY_TOOL: Record<string, SketchTool> = {
	p: "pen",
	r: "rect",
	o: "ellipse",
	l: "line",
	a: "arrow",
};

// --- drawing ----------------------------------------------------------------------

function ElementView({
	el,
	w,
	h,
	last = true,
}: {
	el: SketchElement;
	w: number;
	h: number;
	last?: boolean;
}) {
	const sw = el.width * Math.min(w, h);
	const stroke = sketchColor(el.stroke);
	switch (el.type) {
		case "path":
			return <path d={freehandPath(el.points, sw, w, h, last)} fill={stroke} />;
		case "rect":
			return (
				<rect
					x={el.x * w}
					y={el.y * h}
					width={el.w * w}
					height={el.h * h}
					rx={Math.min(sw * 1.5, (el.w * w) / 2, (el.h * h) / 2)}
					fill={sketchColor(el.fill)}
					stroke={stroke}
					strokeWidth={sw}
					strokeLinejoin="round"
				/>
			);
		case "ellipse":
			return (
				<ellipse
					cx={(el.x + el.w / 2) * w}
					cy={(el.y + el.h / 2) * h}
					rx={(el.w / 2) * w}
					ry={(el.h / 2) * h}
					fill={sketchColor(el.fill)}
					stroke={stroke}
					strokeWidth={sw}
				/>
			);
		case "line":
		case "arrow": {
			const [[x1, y1], [x2, y2]] = el.points;
			const a: [number, number] = [x1 * w, y1 * h];
			const b: [number, number] = [x2 * w, y2 * h];
			const d = el.type === "arrow" ? arrowPath(a, b, sw) : `M${a[0]} ${a[1]}L${b[0]} ${b[1]}`;
			return (
				<path
					d={d}
					fill="none"
					stroke={stroke}
					strokeWidth={sw}
					strokeLinecap="round"
					strokeLinejoin="round"
				/>
			);
		}
	}
}

// Committed elements re-render only when the value does, never per move.
const Committed = React.memo(function Committed({
	elements,
	w,
	h,
}: {
	elements: SketchElement[];
	w: number;
	h: number;
}) {
	return (
		<g data-slot="sketch-board-elements">
			{elements.map((el, i) => (
				// Elements only append, undo or clear: the index is a stable key.
				<ElementView key={i} el={el} w={w} h={h} />
			))}
		</g>
	);
});

// --- toolbar parts ------------------------------------------------------------------

function Hint({
	text,
	keys,
	children,
}: {
	text: string;
	keys?: string[];
	children: React.ReactElement;
}) {
	return (
		<Tooltip>
			<TooltipTrigger asChild>{children}</TooltipTrigger>
			<TooltipContent side="top" className="flex items-center gap-2">
				{text}
				{keys && <Shortcut keys={keys} variant="ghost" size="sm" />}
			</TooltipContent>
		</Tooltip>
	);
}

function Swatch({ color, className }: { color: string; className?: string }) {
	if (color === "none") {
		return (
			<span
				aria-hidden
				className={cn(
					"relative inline-block size-4 overflow-hidden rounded-full border border-border-strong",
					className,
				)}
			>
				<span className="absolute top-1/2 left-1/2 h-px w-[140%] -translate-x-1/2 -translate-y-1/2 -rotate-45 bg-status-danger" />
			</span>
		);
	}
	return (
		<span
			aria-hidden
			className={cn("inline-block size-4 rounded-full border border-border-strong/60", className)}
			style={{ background: sketchColor(color) }}
		/>
	);
}

type BtnSize = "sm" | "md";

function ColorPicker({
	label,
	value,
	colors,
	size,
	onPick,
}: {
	label: string;
	value: string;
	colors: readonly string[];
	size: BtnSize;
	onPick: (c: string) => void;
}) {
	const [open, setOpen] = React.useState(false);
	return (
		<Popover open={open} onOpenChange={setOpen}>
			<Hint text={label}>
				<PopoverTrigger asChild>
					<IconButton variant="ghost" size={size} aria-label={label} data-sketch-control={label}>
						<Swatch color={value} className={size === "sm" ? "size-3.5" : undefined} />
					</IconButton>
				</PopoverTrigger>
			</Hint>
			<PopoverContent side="top" className="w-auto p-1.5">
				<fieldset className="flex gap-0.5">
					<legend className="sr-only">{label}</legend>
					{colors.map((c) => (
						<button
							key={c}
							type="button"
							aria-pressed={c === value}
							aria-label={c}
							title={c}
							className={cn(
								"flex size-7 items-center justify-center rounded-md cursor-default",
								"transition-colors duration-fast ease-out hover:bg-bg-hover active:bg-bg-press",
								"aria-pressed:bg-bg-press",
								"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
							)}
							onClick={() => {
								onPick(c);
								setOpen(false);
							}}
						>
							<Swatch color={c} />
						</button>
					))}
				</fieldset>
			</PopoverContent>
		</Popover>
	);
}

const dot = (size: number) => Math.round(3 + (size / SKETCH_SIZES[SKETCH_SIZES.length - 1]) * 11);

function SizePicker({
	value,
	size,
	onPick,
}: {
	value: number;
	size: BtnSize;
	onPick: (n: number) => void;
}) {
	const [open, setOpen] = React.useState(false);
	return (
		<Popover open={open} onOpenChange={setOpen}>
			<Hint text="Stroke size">
				<PopoverTrigger asChild>
					<IconButton
						variant="ghost"
						size={size}
						aria-label="Stroke size"
						data-sketch-control="size"
					>
						<span
							aria-hidden
							className="rounded-full bg-current"
							style={{ width: Math.min(dot(value), 12), height: Math.min(dot(value), 12) }}
						/>
					</IconButton>
				</PopoverTrigger>
			</Hint>
			<PopoverContent side="top" className="w-auto p-1.5">
				<fieldset className="flex gap-0.5">
					<legend className="sr-only">Stroke size</legend>
					{SKETCH_SIZES.map((s) => (
						<button
							key={s}
							type="button"
							aria-pressed={Math.abs(s - value) < 1e-9}
							aria-label={`Size ${s}`}
							className={cn(
								"flex size-8 items-center justify-center rounded-md cursor-default text-text-primary",
								"transition-colors duration-fast ease-out hover:bg-bg-hover active:bg-bg-press",
								"aria-pressed:bg-bg-press",
								"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
							)}
							onClick={() => {
								onPick(s);
								setOpen(false);
							}}
						>
							<span
								aria-hidden
								className="rounded-full bg-current"
								style={{ width: dot(s), height: dot(s) }}
							/>
						</button>
					))}
				</fieldset>
			</PopoverContent>
		</Popover>
	);
}

function ToolButton({
	tool,
	active,
	size,
	onPick,
}: {
	tool: SketchTool;
	active: boolean;
	size: BtnSize;
	onPick: (t: SketchTool) => void;
}) {
	const meta = TOOL_META[tool];
	const Icon = meta.icon;
	return (
		<Hint text={meta.label} keys={[meta.key]}>
			<button
				type="button"
				aria-label={meta.label}
				aria-pressed={active}
				data-state={active ? "on" : "off"}
				className={toggleVariants({ size })}
				onClick={() => onPick(tool)}
			>
				<Icon aria-hidden />
			</button>
		</Hint>
	);
}

function ShapeMenu({
	shapes,
	tool,
	shown,
	size,
	onPick,
}: {
	shapes: SketchShape[];
	tool: SketchTool;
	shown: SketchShape;
	size: BtnSize;
	onPick: (t: SketchTool) => void;
}) {
	const active = tool !== "pen";
	const Icon = TOOL_META[shown].icon;
	return (
		<DropdownMenu>
			<Hint text="Shapes">
				<DropdownMenuTrigger asChild>
					<button
						type="button"
						aria-label="Shapes"
						data-state={active ? "on" : "off"}
						className={cn(toggleVariants({ size }), "gap-0.5 px-1")}
					>
						<Icon aria-hidden />
						<ChevronDown aria-hidden className="size-3! opacity-60" />
					</button>
				</DropdownMenuTrigger>
			</Hint>
			<DropdownMenuContent side="top" align="center" className="min-w-40">
				{shapes.map((s) => {
					const meta = TOOL_META[s];
					const ItemIcon = meta.icon;
					return (
						<DropdownMenuItem
							key={s}
							data-active={s === tool || undefined}
							className="data-active:bg-bg-press"
							onSelect={() => onPick(s)}
						>
							<ItemIcon aria-hidden />
							{meta.label}
							<DropdownMenuShortcut keys={[meta.key]} />
						</DropdownMenuItem>
					);
				})}
			</DropdownMenuContent>
		</DropdownMenu>
	);
}

// --- the board ----------------------------------------------------------------------

export function SketchBoard({
	value,
	onValueChange,
	width = 280,
	height,
	tools: toolsProp,
	controls: controlsProp,
	defaults: defaultsProp,
	readonly = false,
	label = "Sketch board",
	className,
	style,
	...props
}: SketchBoardProps) {
	const W = width > 0 ? width : 280;
	const H = height && height > 0 ? height : W;
	const config = React.useMemo(
		() => sketchConfig({ tools: toolsProp, controls: controlsProp, defaults: defaultsProp }),
		// Compared by content, not identity: a parent may rebuild the arrays per render.
		[JSON.stringify([toolsProp, controlsProp, defaultsProp])],
	);
	const { tools, controls, defaults } = config;
	const elements = React.useMemo(() => normalizeElements(value, defaults), [value, defaults]);

	// What the person picked. Local, never on the wire; a new default resets it.
	const [tool, setTool] = React.useState<SketchTool>(defaults.tool);
	const [stroke, setStroke] = React.useState(defaults.stroke);
	const [fill, setFill] = React.useState(defaults.fill);
	const [size, setSize] = React.useState(defaults.size);
	const shapes = SKETCH_SHAPES.filter((s) => tools.includes(s));
	const [lastShape, setLastShape] = React.useState<SketchShape>(shapes[0] ?? "rect");
	React.useEffect(() => {
		setTool(defaults.tool);
		setStroke(defaults.stroke);
		setFill(defaults.fill);
		setSize(defaults.size);
	}, [defaults]);
	const activeTool = tools.includes(tool) ? tool : tools[0];

	const pick = (t: SketchTool) => {
		if (!tools.includes(t)) return;
		setTool(t);
		if (t !== "pen") setLastShape(t);
	};

	// History over this board's own commits. `emitted` is the last value this
	// board handed out: a value that is not it came from outside.
	const latest = React.useRef<SketchElement[]>(elements);
	const emitted = React.useRef<unknown>(value);
	const past = React.useRef<SketchElement[][]>([]);
	const future = React.useRef<SketchElement[][]>([]);
	const [, bump] = React.useReducer((n: number) => n + 1, 0);
	if (value !== emitted.current) {
		emitted.current = value;
		latest.current = elements;
		past.current = [];
		future.current = [];
	}

	const emit = (next: SketchElement[]) => {
		latest.current = next;
		emitted.current = next;
		onValueChange?.(next);
		bump();
	};
	const commit = (next: SketchElement[]) => {
		past.current = [...past.current.slice(-(HISTORY - 1)), latest.current];
		future.current = [];
		emit(next);
	};
	const undo = () => {
		const prev = past.current.at(-1);
		if (!prev) return;
		past.current = past.current.slice(0, -1);
		future.current = [latest.current, ...future.current];
		emit(prev);
	};
	const redo = () => {
		const next = future.current[0];
		if (!next) return;
		future.current = future.current.slice(1);
		past.current = [...past.current, latest.current];
		emit(next);
	};
	const clear = () => {
		if (latest.current.length) commit([]);
	};

	// --- pointer ---
	const surfaceRef = React.useRef<HTMLDivElement>(null);
	const rootRef = React.useRef<HTMLDivElement>(null);
	const draft = React.useRef<{
		id: number;
		origin: [number, number];
		el: SketchElement;
	} | null>(null);
	const [, redraw] = React.useReducer((n: number) => n + 1, 0);

	const at = (e: { clientX: number; clientY: number }): [number, number] | null => {
		const box = surfaceRef.current?.getBoundingClientRect();
		if (!box || box.width === 0 || box.height === 0) return null;
		return [
			round(clamp01((e.clientX - box.left) / box.width)),
			round(clamp01((e.clientY - box.top) / box.height)),
		];
	};
	const withPressure = (
		p: [number, number],
		e: { pointerType: string; pressure: number },
	): SketchPoint =>
		e.pointerType === "pen" && e.pressure > 0 ? [p[0], p[1], round(e.pressure)] : p;

	const shaped = (t: SketchShape, a: [number, number], b: [number, number], square: boolean) => {
		let [x2, y2] = b;
		if (t === "line" || t === "arrow") {
			if (square) {
				// Snap to the nearest 45 degrees, in board pixels.
				const dx = (x2 - a[0]) * W;
				const dy = (y2 - a[1]) * H;
				const ang = Math.round(Math.atan2(dy, dx) / (Math.PI / 4)) * (Math.PI / 4);
				const len = Math.hypot(dx, dy);
				x2 = clamp01(a[0] + (Math.cos(ang) * len) / W);
				y2 = clamp01(a[1] + (Math.sin(ang) * len) / H);
			}
			return { type: t, points: [a, [round(x2), round(y2)]], stroke, width: size } as SketchElement;
		}
		if (square) {
			const side = Math.max(Math.abs(x2 - a[0]) * W, Math.abs(y2 - a[1]) * H);
			x2 = clamp01(a[0] + (Math.sign(x2 - a[0]) || 1) * (side / W));
			y2 = clamp01(a[1] + (Math.sign(y2 - a[1]) || 1) * (side / H));
		}
		return {
			type: t,
			x: round(Math.min(a[0], x2)),
			y: round(Math.min(a[1], y2)),
			w: round(Math.abs(x2 - a[0])),
			h: round(Math.abs(y2 - a[1])),
			stroke,
			fill,
			width: size,
		} as SketchElement;
	};

	const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
		if (readonly || draft.current) return;
		if (e.pointerType === "mouse" && e.button !== 0) return;
		const p = at(e);
		if (!p) return;
		e.preventDefault();
		rootRef.current?.focus({ preventScroll: true });
		try {
			e.currentTarget.setPointerCapture?.(e.pointerId);
		} catch {
			// A pointer the browser no longer tracks (a synthetic or replayed
			// event): draw without capture rather than drop the element.
		}
		const el: SketchElement =
			activeTool === "pen"
				? { type: "path", points: [withPressure(p, e)], stroke, width: size }
				: shaped(activeTool, p, p, false);
		draft.current = { id: e.pointerId, origin: p, el };
		redraw();
	};

	const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
		const d = draft.current;
		if (!d || d.id !== e.pointerId) return;
		if (d.el.type === "path") {
			const pts = d.el.points;
			const events = e.nativeEvent.getCoalescedEvents?.() ?? [];
			for (const ev of events.length ? events : [e.nativeEvent]) {
				const p = at(ev);
				if (!p) continue;
				const last = pts[pts.length - 1];
				if (Math.hypot(p[0] - last[0], p[1] - last[1]) < MIN_STEP) continue;
				pts.push(withPressure(p, ev));
			}
		} else {
			const p = at(e);
			if (p) d.el = shaped(d.el.type, d.origin, p, e.shiftKey);
		}
		redraw();
	};

	const finish = (keep: boolean) => {
		const d = draft.current;
		draft.current = null;
		redraw();
		if (!keep || !d) return;
		const el = d.el;
		if (el.type === "rect" || el.type === "ellipse") {
			if (el.w < MIN_SHAPE && el.h < MIN_SHAPE) return;
		} else if (el.type === "line" || el.type === "arrow") {
			const [[x1, y1], [x2, y2]] = el.points;
			if (Math.hypot(x2 - x1, y2 - y1) < MIN_SHAPE) return;
		}
		commit([...latest.current, el]);
	};

	const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
		if (draft.current?.id !== e.pointerId) return;
		onPointerMove(e);
		finish(true);
	};
	// The browser took the pointer (a system gesture, a lost capture). Keep
	// what was drawn: ink the person saw land should not vanish.
	const onPointerCancel = (e: React.PointerEvent<HTMLDivElement>) => {
		if (draft.current?.id === e.pointerId) finish(true);
	};

	// Made read-only mid-stroke: drop the element in flight.
	React.useEffect(() => {
		if (readonly && draft.current) finish(false);
	});

	// Bound natively rather than as a prop: the root is a drawing surface, not
	// a control, and the handler reads this render's state through the ref.
	const handleKey = (e: KeyboardEvent) => {
		if (e.defaultPrevented || readonly) return;
		const mod = e.metaKey || e.ctrlKey;
		const key = e.key.toLowerCase();
		if (mod && key === "z") {
			e.preventDefault();
			if (e.shiftKey) redo();
			else undo();
			return;
		}
		if (mod && key === "y") {
			e.preventDefault();
			redo();
			return;
		}
		if (e.key === "Escape" && draft.current) {
			e.preventDefault();
			finish(false);
			return;
		}
		if (mod || e.altKey) return;
		const t = KEY_TOOL[key];
		if (t && tools.includes(t)) {
			e.preventDefault();
			pick(t);
		}
	};

	const keyRef = React.useRef(handleKey);
	keyRef.current = handleKey;
	React.useEffect(() => {
		const root = rootRef.current;
		if (!root) return;
		const listener = (e: KeyboardEvent) => keyRef.current(e);
		root.addEventListener("keydown", listener);
		return () => root.removeEventListener("keydown", listener);
	}, []);

	// --- toolbar ---
	const has = (c: SketchControl) => controls.includes(c);
	const btn: BtnSize = W < 420 ? "sm" : "md";
	const showTools = has("tools") && tools.length > 1;
	const groupA = [
		showTools && tools.includes("pen") && (
			<ToolButton key="pen" tool="pen" active={activeTool === "pen"} size={btn} onPick={pick} />
		),
		showTools && shapes.length === 1 && (
			<ToolButton
				key="shape"
				tool={shapes[0]}
				active={activeTool === shapes[0]}
				size={btn}
				onPick={pick}
			/>
		),
		showTools && shapes.length > 1 && (
			<ShapeMenu
				key="shapes"
				shapes={shapes}
				tool={activeTool}
				shown={activeTool !== "pen" ? activeTool : lastShape}
				size={btn}
				onPick={pick}
			/>
		),
	].filter(Boolean);
	const groupB = [
		has("stroke") && (
			<ColorPicker
				key="stroke"
				label="Stroke color"
				value={stroke}
				colors={SKETCH_STROKES}
				size={btn}
				onPick={setStroke}
			/>
		),
		has("fill") && shapes.some((s) => s === "rect" || s === "ellipse") && (
			<ColorPicker
				key="fill"
				label="Fill color"
				value={fill}
				colors={SKETCH_FILLS}
				size={btn}
				onPick={setFill}
			/>
		),
		has("size") && <SizePicker key="size" value={size} size={btn} onPick={setSize} />,
	].filter(Boolean);
	const groupC = [
		has("undo") && (
			<Hint key="undo" text="Undo" keys={["mod", "Z"]}>
				<IconButton
					variant="ghost"
					size={btn}
					aria-label="Undo"
					disabled={past.current.length === 0}
					onClick={undo}
				>
					<Undo2 aria-hidden />
				</IconButton>
			</Hint>
		),
		has("redo") && (
			<Hint key="redo" text="Redo" keys={["mod", "shift", "Z"]}>
				<IconButton
					variant="ghost"
					size={btn}
					aria-label="Redo"
					disabled={future.current.length === 0}
					onClick={redo}
				>
					<Redo2 aria-hidden />
				</IconButton>
			</Hint>
		),
		has("clear") && (
			<Hint key="clear" text="Clear">
				<IconButton
					variant="ghost"
					size={btn}
					aria-label="Clear"
					disabled={elements.length === 0}
					onClick={clear}
				>
					<Trash2 aria-hidden />
				</IconButton>
			</Hint>
		),
	].filter(Boolean);
	const groups = [groupA, groupB, groupC].filter((g) => g.length > 0);
	const toolbar = !readonly && groups.length > 0;

	const d = draft.current;
	const count = elements.length;
	const sep = <Separator orientation="vertical" className="mx-0.5 h-4" />;

	return (
		<div
			ref={rootRef}
			data-slot="sketch-board"
			data-readonly={readonly || undefined}
			data-drawing={d ? true : undefined}
			tabIndex={readonly ? undefined : 0}
			className={cn(
				"group/sketch relative max-w-full rounded-lg outline-hidden",
				"focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
				className,
			)}
			style={{ width: W, aspectRatio: `${W} / ${H}`, ...style }}
			{...props}
		>
			<div
				ref={surfaceRef}
				data-slot="sketch-board-surface"
				role="img"
				aria-label={`${label}, ${count === 0 ? "blank" : `${count} ${count === 1 ? "element" : "elements"}`}`}
				className={cn(
					"absolute inset-0 overflow-hidden rounded-lg border",
					"bg-bg-surface text-text-primary border-border-default",
					"transition-[border-color] duration-fast ease-out",
					readonly
						? "cursor-default"
						: "touch-none select-none cursor-crosshair hover:border-border-strong group-data-[drawing]/sketch:border-border-strong",
				)}
				onPointerDown={readonly ? undefined : onPointerDown}
				onPointerMove={readonly ? undefined : onPointerMove}
				onPointerUp={readonly ? undefined : onPointerUp}
				onPointerCancel={readonly ? undefined : onPointerCancel}
			>
				<svg
					aria-hidden="true"
					viewBox={`0 0 ${W} ${H}`}
					preserveAspectRatio="none"
					className="pointer-events-none block size-full"
				>
					<Committed elements={elements} w={W} h={H} />
					{d && (
						<g data-slot="sketch-board-draft">
							<ElementView el={d.el} w={W} h={H} last={false} />
						</g>
					)}
				</svg>
			</div>
			{toolbar && (
				<TooltipProvider>
					<div
						data-slot="sketch-board-toolbar"
						role="toolbar"
						aria-label={`${label} tools`}
						className={cn(
							"absolute bottom-2 left-1/2 flex -translate-x-1/2 items-center gap-0.5 rounded-lg p-1",
							"border border-border-default bg-bg-elevated text-text-secondary shadow-floating",
						)}
					>
						{groups.map((g, i) => (
							<React.Fragment key={i === 0 ? "a" : i === 1 ? "b" : "c"}>
								{i > 0 && sep}
								{g}
							</React.Fragment>
						))}
					</div>
				</TooltipProvider>
			)}
		</div>
	);
}
