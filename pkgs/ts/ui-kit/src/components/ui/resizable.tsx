// Resizable: split panels with drag handles between them.
//
// Design refs:
//   cursor.md   resizers: col-resize / row-resize, arrow everywhere else
//   palette.md  the handle is the `border-subtle` hairline, the drag line
//               `accent` (the same line as the sidebar's edge handle)
//   a11y.md     §1 focus ring on the handle; window splitter pattern:
//               role separator, aria-valuenow / min / max, arrows step,
//               Home / End to the bounds, Enter folds a collapsible panel
//
// ## Shape
//
//   <ResizablePanelGroup orientation="horizontal" storageKey="app.split">
//     <ResizablePanel defaultSize={25} minSize="180px" collapsible>…</ResizablePanel>
//     <ResizableHandle />
//     <ResizablePanel>…</ResizablePanel>
//   </ResizablePanelGroup>
//
// Panels and handles are the group's direct children, in order; a handle
// moves the border between the panel before it and the panel after it. A
// group inside a panel is a new, independent split, which is how a vertical
// stack sits in one column of a horizontal one.
//
// ## Sizes
//
// The group keeps one percentage per panel, summing to 100, and each panel
// is `flex: <size> 1 0px`, so the panels share whatever the handles leave in
// proportion and a resized window keeps the shape. Bounds take a number (a
// percentage), "N%" or "Npx". A px bound is also set as the panel's CSS min
// or max, so the browser holds it while the window resizes; the drag math
// turns it into a percentage of the measured group as it goes.
//
// A panel with no `defaultSize` takes an equal share of what the others leave.
// A px `defaultSize` is resolved once the group is measured, before the first
// paint, and makes the panel hold its px size when the group resizes: the
// panels without one take up the difference. That is a sidebar, which keeps
// its width while the window changes and the main panel flexes.
// A drag moves exactly one border: the two neighbours trade size within their
// bounds and nobody else moves. A collapsible panel dragged more than halfway
// below its minimum folds to `collapsedSize` (0 by default), and the panel
// remembers the size it folded from for Enter to bring it back.
//
// A panel keeps its size when the panels only change order: with an `id` on
// each, a panel moved elsewhere in the group takes its size along. A panel
// added or removed starts the group over from its defaults.
//
// ## Overflow
//
// `overflow="fit"` (the default) is the above: the panels always fill the
// group exactly. `overflow="scroll"` is a desk instead: a panel never
// squeezes under its minimum, and when the minimums add up to more than the
// group has, the group scrolls along its axis. Sizes are still percentages
// of what the group shows (less the handles), but they may add up to more
// than 100: a drag lets the panel before the border take what it asks for
// within its bounds, the panel after gives it back within its own, and past
// that the content grows or shrinks rather than the drag stopping. Each panel
// is `flex: <size> 0 <size>%`, so a resized window keeps the shape and a
// narrow one scrolls rather than squeezing. With no `maxSize` a panel has no
// ceiling here.
//
// ## Memory
//
// `storageKey` keeps the layout in localStorage the way `useResizableWidth`
// keeps a width: read once on mount, written when a change lands (end of a
// drag, a key, a reset), every access guarded. A stored layout that no longer
// fits the panels (count changed, garbage) is ignored. What is kept is the
// sizes, the length they were laid out on (so a px-held panel comes back at
// the same px in a different window) and the size each folded panel will
// unfold to, so a panel folded before a reload still opens to its width.
// Double-clicking a handle puts the whole group back to its default sizes.
//
// A panel folded to nothing is `inert`: nothing in it takes focus or a click
// while it cannot be seen, and it stays mounted.

import type * as React from "react";
import {
	Children,
	createContext,
	isValidElement,
	useCallback,
	useContext,
	useEffect,
	useId,
	useImperativeHandle,
	useLayoutEffect,
	useMemo,
	useRef,
	useState,
} from "react";
import { useKeyScope } from "../../lib/keyboard";
import { readStored, splitHandleClasses, trackDrag, writeStored } from "../../lib/resize";
import { cn } from "../../lib/utils";

/** A panel bound or size: a number is a percentage, or "N%" / "Npx". */
export type ResizableSize = number | `${number}%` | `${number}px`;

export type ResizableOrientation = "horizontal" | "vertical";

/** Fill the group exactly, or scroll when the minimums do not fit. */
export type ResizableOverflow = "fit" | "scroll";

/** Imperative access to a group, for a toggle button outside it. */
export type ResizablePanelGroupHandle = {
	/** The current sizes, percentages in panel order. */
	getLayout: () => number[];
	/** Set every size at once; bounds are applied, and a filling group scales the rest to 100. */
	setLayout: (sizes: number[]) => void;
	/** Back to the default sizes. */
	reset: () => void;
	/** Fold panel `index`; a no-op unless it is collapsible. */
	collapse: (index: number) => void;
	/** Unfold panel `index` to the size it folded from. */
	expand: (index: number) => void;
	isCollapsed: (index: number) => boolean;
};

export interface ResizablePanelGroupProps extends Omit<React.ComponentProps<"div">, "ref"> {
	orientation?: ResizableOrientation;
	/** "scroll" lets the panels outgrow the group, which scrolls. Default "fit". */
	overflow?: ResizableOverflow;
	/** The group's own element, for a consumer that scrolls or measures it. */
	elementRef?: React.Ref<HTMLDivElement>;
	/** localStorage key that remembers the layout across reloads. */
	storageKey?: string;
	/** How far an arrow key moves a border, in percent. Default 5. */
	keyboardStep?: number;
	/** Called with the sizes whenever a change lands. */
	onLayout?: (sizes: number[]) => void;
	ref?: React.Ref<ResizablePanelGroupHandle>;
}

export interface ResizablePanelProps extends React.ComponentProps<"div"> {
	/**
	 * A percentage, or "Npx": resolved once the group is measured, and the
	 * panel then holds its px size when the group resizes.
	 */
	defaultSize?: ResizableSize;
	minSize?: ResizableSize;
	maxSize?: ResizableSize;
	/** Dragging well below the minimum folds the panel. */
	collapsible?: boolean;
	/** The folded size. Default 0. */
	collapsedSize?: ResizableSize;
}

export interface ResizableHandleProps extends React.ComponentProps<"div"> {}

/** The size a folded panel unfolds to, and the group length it was taken on. */
type Unfold = { size: number; span: number };

/** What a group keeps: its sizes, laid out for `ids` on a group `span` px long. */
type Layout = { ids: string[]; sizes: number[]; span: number };

type Group = {
	orientation: ResizableOrientation;
	overflow: ResizableOverflow;
	sizes: number[];
	ids: string[];
	bounds: Bound[];
	onHandleDown: (e: React.PointerEvent, before: number) => void;
	onHandleKey: (before: number, action: KeyAction) => void;
	reset: () => void;
	dragging: number | null;
};

type KeyAction = "less" | "more" | "min" | "max" | "toggle";

type Bound = {
	min: number;
	max: number;
	collapsible: boolean;
	collapsed: number;
};

const GroupContext = createContext<Group | null>(null);
/** The position of a panel among the panels, or of the panel before a handle. */
const IndexContext = createContext(-1);

function useGroup(part: string): Group {
	const group = useContext(GroupContext);
	if (!group) throw new Error(`${part} must be a direct child of ResizablePanelGroup`);
	return group;
}

/** `size` as a percentage of `total` px; `total` 0 (not measured) drops px. */
function toPct(size: ResizableSize | undefined, total: number, fallback: number): number {
	if (size === undefined) return fallback;
	if (typeof size === "number") return size;
	const n = Number.parseFloat(size);
	if (!Number.isFinite(n)) return fallback;
	if (size.endsWith("px")) return total > 0 ? (n / total) * 100 : fallback;
	return n;
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

const isPx = (size: ResizableSize | undefined) => typeof size === "string" && size.endsWith("px");

/**
 * `sizes`, laid out on a group `from` px long, for one `to` px long: each
 * `held` panel keeps its px, the others share what is left in proportion.
 */
function hold(sizes: number[], held: boolean[], from: number, to: number): number[] {
	if (from <= 0 || to <= 0 || from === to || !held.some(Boolean)) return sizes;
	const out = sizes.map((s, i) => (held[i] ? (s * from) / to : s));
	const fixed = out.reduce((a, s, i) => a + (held[i] ? s : 0), 0);
	const rest = sizes.reduce((a, s, i) => a + (held[i] ? 0 : s), 0);
	if (rest <= 0) return out;
	const scale = Math.max(0, 100 - fixed) / rest;
	return out.map((s, i) => (held[i] ? s : s * scale));
}

/** Where a panel lands when something asks for `want`, folding if it may. */
function fit(want: number, b: Bound): number {
	if (b.collapsible && want < b.collapsed + (b.min - b.collapsed) / 2) return b.collapsed;
	return clamp(want, b.min, b.max);
}

/** Scale `sizes` so they sum to 100. */
function normalize(sizes: number[]): number[] {
	const sum = sizes.reduce((a, b) => a + b, 0);
	return sum > 0 ? sizes.map((s) => (s / sum) * 100) : sizes.map(() => 100 / sizes.length);
}

/**
 * Move the border between `before` and `before + 1` by `delta` percent. The
 * two trade size within their bounds; every other panel stays put.
 */
function moveBorder(sizes: number[], before: number, delta: number, bounds: Bound[]): number[] {
	const l = before;
	const r = before + 1;
	const pair = sizes[l] + sizes[r];
	let left = fit(sizes[l] + delta, bounds[l]);
	const right = fit(pair - left, bounds[r]);
	left = clamp(pair - right, Math.min(bounds[l].collapsed, bounds[l].min), bounds[l].max);
	const next = [...sizes];
	next[l] = left;
	next[r] = pair - left;
	return next;
}

/**
 * The scroll mode's border: the panel before it takes `delta` within its
 * bounds, the one after gives the same back within its own, and whatever
 * neither can absorb grows or shrinks the content. Every other panel stays.
 */
function pushBorder(sizes: number[], before: number, delta: number, bounds: Bound[]): number[] {
	const l = before;
	const r = before + 1;
	const left = fit(sizes[l] + delta, bounds[l]);
	const next = [...sizes];
	next[l] = left;
	next[r] = fit(sizes[r] - (left - sizes[l]), bounds[r]);
	return next;
}

/**
 * `sizes` (laid out for `from`) rearranged for `to`, when `to` is the same
 * panels in any order; null when a panel came or went.
 */
function rearrange(from: string[], sizes: number[], to: string[]): number[] | null {
	if (from.length !== to.length) return null;
	const at = new Map(from.map((id, i) => [id, sizes[i]]));
	const out = to.map((id) => at.get(id));
	return out.every((s) => s !== undefined) ? (out as number[]) : null;
}

const PANELS = ":scope > [data-slot=resizable-panel]";
const HANDLES = ":scope > [data-slot=resizable-handle]";

function sameLength(a: unknown, n: number): a is number[] {
	return (
		Array.isArray(a) &&
		a.length === n &&
		a.every((v) => typeof v === "number" && Number.isFinite(v))
	);
}

export function ResizablePanelGroup({
	orientation = "horizontal",
	overflow = "fit",
	elementRef,
	storageKey,
	keyboardStep = 5,
	onLayout,
	ref,
	className,
	style,
	children,
	...props
}: ResizablePanelGroupProps) {
	const groupId = useId();
	const rootRef = useRef<HTMLDivElement>(null);
	const axis = orientation === "horizontal" ? "x" : "y";
	const scroll = overflow === "scroll";

	// The panels' props, read straight off the children so the group knows
	// every bound and default before anything renders.
	const parts = Children.toArray(children).filter(isValidElement);
	const panels = parts
		.filter((c) => c.type === ResizablePanel)
		.map((c) => c.props as ResizablePanelProps);
	const count = panels.length;
	const ids = panels.map((p, i) => p.id ?? `${groupId}-panel-${i}`);
	const shape = ids.join("|");
	const panelsRef = useRef(panels);
	panelsRef.current = panels;
	const idsRef = useRef(ids);
	idsRef.current = ids;

	const setRoot = useCallback(
		(el: HTMLDivElement | null) => {
			rootRef.current = el;
			if (typeof elementRef === "function") elementRef(el);
			else if (elementRef) elementRef.current = el;
		},
		[elementRef],
	);

	/** The total length of the root's children matching `selector`. */
	const lengthOf = useCallback(
		(selector: string): number => {
			const root = rootRef.current;
			if (!root) return 0;
			let total = 0;
			for (const el of root.querySelectorAll<HTMLElement>(selector)) {
				const rect = el.getBoundingClientRect();
				total += axis === "x" ? rect.width : rect.height;
			}
			return total;
		},
		[axis],
	);

	// What percentages are of, less the handles: the panels' length when they
	// fill the group, what the group shows when it scrolls. Kept for the aria
	// bounds; a drag measures afresh.
	const [span, setSpan] = useState(0);
	const measure = useCallback((): number => {
		const root = rootRef.current;
		if (!root) return 0;
		if (!scroll) return lengthOf(PANELS);
		const shown = axis === "x" ? root.clientWidth : root.clientHeight;
		return Math.max(0, shown - lengthOf(HANDLES));
	}, [scroll, axis, lengthOf]);
	useEffect(() => {
		const root = rootRef.current;
		if (!root || typeof ResizeObserver === "undefined") return;
		const observer = new ResizeObserver(() => setSpan(measure()));
		observer.observe(root);
		return () => observer.disconnect();
	}, [measure]);
	// Once before the first paint as well, so a px default never flashes.
	useLayoutEffect(() => setSpan(measure()), [measure, shape]);

	// A scrolling group's panels take their share of what the handles leave,
	// in CSS, so the handles are measured before the first paint.
	const [handles, setHandles] = useState(0);
	useLayoutEffect(() => {
		if (scroll) setHandles(lengthOf(HANDLES));
	}, [scroll, lengthOf, shape]);

	const boundsAt = useCallback(
		(total: number): Bound[] => {
			const ceiling = scroll ? Number.POSITIVE_INFINITY : 100;
			return panelsRef.current.map((p) => {
				const min = clamp(toPct(p.minSize, total, 0), 0, ceiling);
				return {
					min,
					max: clamp(toPct(p.maxSize, total, ceiling), min, ceiling),
					collapsible: !!p.collapsible,
					collapsed: clamp(toPct(p.collapsedSize, total, 0), 0, min),
				};
			});
		},
		[scroll],
	);
	const bounds = boundsAt(span);

	// Panels without a default share what the others leave, equally. A px
	// default not yet measured shares too, for the one render before the
	// layout effect above measures the group.
	const defaultsAt = useCallback((total: number): number[] => {
		const given = panelsRef.current.map((p) => {
			const s = toPct(p.defaultSize, total, Number.NaN);
			return Number.isFinite(s) ? s : null;
		});
		const taken = given.reduce<number>((a, s) => a + (s ?? 0), 0);
		const open = given.filter((s) => s === null).length;
		const share = open > 0 ? Math.max(0, 100 - taken) / open : 0;
		return normalize(given.map((s) => s ?? share));
	}, []);
	const defaults = useMemo(() => defaultsAt(span), [defaultsAt, span, shape]);

	// Panels with a px default hold their px when the group resizes (fit only:
	// a scrolling group has no length to share out).
	const held = panels.map((p) => !scroll && isPx(p.defaultSize));

	// A scrolling group's sizes may add up to more than 100, so they are kept
	// as they are; a filling group's always come back to 100.
	const settle = useCallback((s: number[]) => (scroll ? s : normalize(s)), [scroll]);

	// What storage holds: `{ sizes, span, unfolded }`, or a bare array of
	// sizes. Read once, on mount.
	const [stored] = useState<{ layout: Layout | null; unfolded: Record<string, Unfold> }>(() => {
		const none = { layout: null, unfolded: {} };
		if (!storageKey) return none;
		try {
			const raw: unknown = JSON.parse(readStored(storageKey) ?? "null");
			const kept = (Array.isArray(raw) ? { sizes: raw } : (raw ?? {})) as {
				sizes?: unknown;
				span?: unknown;
				unfolded?: unknown;
			};
			if (!sameLength(kept.sizes, count) || kept.sizes.some((s) => s < 0)) return none;
			const span = typeof kept.span === "number" && kept.span > 0 ? kept.span : 0;
			const unfolded: Record<string, Unfold> = {};
			if (kept.unfolded && typeof kept.unfolded === "object") {
				for (const [id, u] of Object.entries(kept.unfolded as Record<string, Unfold>)) {
					if (Number.isFinite(u?.size) && Number.isFinite(u?.span)) unfolded[id] = u;
				}
			}
			return { layout: { ids, sizes: settle(kept.sizes), span }, unfolded };
		} catch {
			return none;
		}
	});

	// Null until something changes the layout: the defaults, followed as the
	// group is measured and resized.
	const [state, setState] = useState<Layout | null>(stored.layout);
	const kept = state ? rearrange(state.ids, state.sizes, ids) : null;
	const sizes = kept && state ? hold(kept, held, state.span, span) : defaults;
	const sizesRef = useRef(sizes);
	sizesRef.current = sizes;
	const heldRef = useRef(held);
	heldRef.current = held;

	// The size each collapsible panel folded from, by id, for Enter / expand.
	const unfolded = useRef<Record<string, Unfold>>(stored.unfolded);

	/** Land `next`, laid out on a group `at` px long (measured when left out). */
	const commit = useCallback(
		(next: number[], save = true, at?: number) => {
			const length = at ?? measure();
			sizesRef.current = next;
			setState({ ids: idsRef.current, sizes: next, span: length });
			if (!save) return;
			if (storageKey) {
				const layout = {
					sizes: next.map((s) => +s.toFixed(3)),
					span: Math.round(length),
					unfolded: unfolded.current,
				};
				writeStored(storageKey, JSON.stringify(layout));
			}
			onLayout?.(next);
		},
		[measure, storageKey, onLayout],
	);

	const reset = useCallback(() => {
		unfolded.current = {};
		const total = measure();
		commit(defaultsAt(total), true, total);
	}, [commit, defaultsAt, measure]);

	const isCollapsed = useCallback(
		(i: number) => !!bounds[i]?.collapsible && sizesRef.current[i] <= bounds[i].collapsed,
		[bounds],
	);

	/** Fold or unfold panel `i`, giving or taking the size from a neighbour. */
	const setFolded = useCallback(
		(i: number, fold: boolean) => {
			const total = measure();
			const b = boundsAt(total);
			const cur = sizesRef.current;
			if (!b[i]?.collapsible || count < 2) return;
			const folded = cur[i] <= b[i].collapsed;
			if (fold === folded) return;
			const id = idsRef.current[i];
			if (fold) unfolded.current[id] = { size: cur[i], span: total };
			const u = unfolded.current[id];
			// A px-held panel unfolds to the px it folded from.
			const back =
				u && heldRef.current[i] && u.span > 0 && total > 0 ? (u.size * u.span) / total : u?.size;
			const want = fold ? b[i].collapsed : (back ?? Math.max(b[i].min, defaultsAt(total)[i]));
			// The neighbour after it pays, or the one before for the last panel.
			const before = i < count - 1 ? i : i - 1;
			const delta = before === i ? want - cur[i] : cur[i] - want;
			const next = [...cur];
			const pair = cur[before] + cur[before + 1];
			next[before] = clamp(cur[before] + delta, 0, pair);
			next[before + 1] = pair - next[before];
			commit(next, true, total);
		},
		[boundsAt, measure, count, defaultsAt, commit],
	);

	const [dragging, setDragging] = useState<number | null>(null);
	const move = scroll ? pushBorder : moveBorder;

	const onHandleDown = useCallback(
		(e: React.PointerEvent, before: number) => {
			if (before < 0 || before >= count - 1) return;
			const total = measure();
			if (total <= 0) return;
			// Start from what is on screen: a px bound in CSS may have moved a
			// panel off its stored share.
			const els = rootRef.current?.querySelectorAll<HTMLElement>(PANELS);
			const start =
				els && els.length === count
					? Array.from(els, (el) => {
							const r = el.getBoundingClientRect();
							return ((axis === "x" ? r.width : r.height) / total) * 100;
						})
					: sizesRef.current;
			const b = boundsAt(total);
			const ids = idsRef.current;
			let last = start;
			trackDrag(
				e,
				axis,
				(d) => {
					setDragging(before);
					last = move(start, before, (d / total) * 100, b);
					if (b[before].collapsible && last[before] <= b[before].collapsed)
						unfolded.current[ids[before]] = { size: start[before], span: total };
					if (b[before + 1].collapsible && last[before + 1] <= b[before + 1].collapsed)
						unfolded.current[ids[before + 1]] = { size: start[before + 1], span: total };
					commit(last, false, total);
				},
				() => {
					setDragging(null);
					commit(last, true, total);
				},
			);
		},
		[count, measure, axis, boundsAt, move, commit],
	);

	const onHandleKey = useCallback(
		(before: number, action: KeyAction) => {
			if (before < 0 || before >= count - 1) return;
			const b = boundsAt(measure());
			const cur = sizesRef.current;
			if (action === "toggle") {
				const target = b[before].collapsible ? before : b[before + 1].collapsible ? before + 1 : -1;
				if (target >= 0) setFolded(target, !(cur[target] <= b[target].collapsed));
				return;
			}
			// No ceiling (a scrolling group's default) means End has nowhere to go.
			if (action === "max" && !Number.isFinite(b[before].max)) return;
			const delta =
				action === "less"
					? -keyboardStep
					: action === "more"
						? keyboardStep
						: action === "min"
							? Math.min(b[before].min, b[before].collapsed) - cur[before]
							: b[before].max - cur[before];
			// Keys move by plain clamping: an arrow step should never fold a
			// panel by surprise, so collapse is Enter's alone.
			const noFold = b.map((x) => ({ ...x, collapsible: false }));
			if (action === "min" && b[before].collapsible) noFold[before] = b[before];
			commit(move(cur, before, delta, noFold));
		},
		[count, boundsAt, measure, keyboardStep, setFolded, move, commit],
	);

	useImperativeHandle(
		ref,
		() => ({
			getLayout: () => [...sizesRef.current],
			setLayout: (next) => {
				if (!sameLength(next, count)) return;
				const b = boundsAt(measure());
				commit(settle(next.map((s, i) => fit(s, b[i]))));
			},
			reset,
			collapse: (i) => setFolded(i, true),
			expand: (i) => setFolded(i, false),
			isCollapsed,
		}),
		[count, boundsAt, measure, commit, settle, reset, setFolded, isCollapsed],
	);

	// A fresh value each render: the panels re-render with the group anyway.
	const group: Group = {
		orientation,
		overflow,
		sizes,
		ids,
		bounds,
		onHandleDown,
		onHandleKey,
		reset,
		dragging,
	};

	// Number the parts in order: each panel its own position, each handle the
	// position of the panel before it.
	let panelAt = -1;
	return (
		<GroupContext.Provider value={group}>
			<div
				ref={setRoot}
				data-slot="resizable-panel-group"
				data-orientation={orientation}
				data-overflow={overflow}
				className={cn(
					"flex size-full",
					orientation === "vertical" && "flex-col",
					!scroll && "overflow-hidden",
					scroll && axis === "x" && "overflow-x-auto overflow-y-hidden",
					scroll && axis === "y" && "overflow-y-auto overflow-x-hidden",
					className,
				)}
				style={
					scroll
						? ({ "--resizable-handles": `${handles}px`, ...style } as React.CSSProperties)
						: style
				}
				{...props}
			>
				{Children.map(children, (child) => {
					if (!isValidElement(child)) return child;
					if (child.type === ResizablePanel) panelAt += 1;
					return <IndexContext.Provider value={panelAt}>{child}</IndexContext.Provider>;
				})}
			</div>
		</GroupContext.Provider>
	);
}

export function ResizablePanel({
	defaultSize: _defaultSize,
	minSize,
	maxSize,
	collapsible,
	collapsedSize: _collapsedSize,
	className,
	style,
	...props
}: ResizablePanelProps) {
	const group = useGroup("ResizablePanel");
	const i = useContext(IndexContext);
	const size = group.sizes[i] ?? 0;
	const folded = !!collapsible && size <= (group.bounds[i]?.collapsed ?? 0);
	const horizontal = group.orientation === "horizontal";
	// px bounds go to CSS too, so the browser holds them while the window
	// resizes. A folded panel drops its minimum or it could not fold.
	const px = (v: ResizableSize | undefined) =>
		typeof v === "string" && v.endsWith("px") ? v : undefined;
	const min = folded ? undefined : px(minSize);
	const max = px(maxSize);
	return (
		<div
			data-slot="resizable-panel"
			data-state={collapsible ? (folded ? "collapsed" : "expanded") : undefined}
			// Folded to nothing: out of reach of focus and clicks, still mounted.
			inert={folded && size <= 0 ? true : undefined}
			id={group.ids[i]}
			className={cn("relative overflow-hidden", className)}
			style={{
				// Scrolling: no shrink, and a basis that is the panel's share
				// of what the group shows less its handles.
				...(group.overflow === "scroll"
					? {
							flexGrow: size,
							flexShrink: 0,
							flexBasis: `calc((100% - var(--resizable-handles, 0px)) * ${size / 100})`,
						}
					: { flex: `${size} 1 0px` }),
				...(horizontal ? { minWidth: min, maxWidth: max } : { minHeight: min, maxHeight: max }),
				...style,
			}}
			{...props}
		/>
	);
}

export function ResizableHandle({
	className,
	onDoubleClick,
	onPointerDown,
	onKeyDown,
	...props
}: ResizableHandleProps) {
	const group = useGroup("ResizableHandle");
	const before = useContext(IndexContext);
	const horizontal = group.orientation === "horizontal";
	const keys = useKeyScope<HTMLDivElement>({
		[horizontal ? "ArrowLeft" : "ArrowUp"]: () => group.onHandleKey(before, "less"),
		[horizontal ? "ArrowRight" : "ArrowDown"]: () => group.onHandleKey(before, "more"),
		Home: () => group.onHandleKey(before, "min"),
		End: () => group.onHandleKey(before, "max"),
		Enter: () => group.onHandleKey(before, "toggle"),
	});
	const b = group.bounds[before];
	return (
		// biome-ignore lint/a11y/useSemanticElements: a focusable splitter, not an <hr>
		<div
			data-slot="resizable-handle"
			data-orientation={group.orientation}
			data-dragging={group.dragging === before ? "" : undefined}
			role="separator"
			// The separator's own orientation: across the group's axis.
			aria-orientation={horizontal ? "vertical" : "horizontal"}
			aria-controls={group.ids[before]}
			aria-valuenow={Math.round(group.sizes[before] ?? 0)}
			aria-valuemin={b ? Math.round(Math.min(b.min, b.collapsed)) : 0}
			aria-valuemax={b ? (Number.isFinite(b.max) ? Math.round(b.max) : undefined) : 100}
			aria-label="Resize"
			className={cn(splitHandleClasses(group.orientation), className)}
			tabIndex={keys.tabIndex}
			onPointerDown={(e) => {
				onPointerDown?.(e);
				if (!e.defaultPrevented) group.onHandleDown(e, before);
			}}
			onDoubleClick={(e) => {
				onDoubleClick?.(e);
				if (!e.defaultPrevented) group.reset();
			}}
			onKeyDown={(e) => {
				onKeyDown?.(e);
				if (!e.defaultPrevented) keys.onKeyDown(e);
			}}
			{...props}
		/>
	);
}
