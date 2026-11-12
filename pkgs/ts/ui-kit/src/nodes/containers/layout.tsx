// Layout -- the four layers every container speaks, read the same way.
//
// The Python `layout` props, one path for every container:
//
//   size      width min_width max_width height min_height max_height, each a
//             length: a number is px, text is a CSS length ("60vh", "20rem")
//             or a page width name ("prose", "main", ...: the theme's
//             container widths; "full" is 100%). `scroll` "y" | "x" |
//             "both" scrolls what runs past the edge.
//   space     `padding` and `gap`, an int step 0..16, 4px each.
//   arrange   `justify` along the main axis, `align` across it.
//   divided   a hairline between children.
//
// A prop arrives only when the program set it. Unset (or null, after a
// `set_layout` that clears it), the container draws its own look: each one
// hands `useLayout` its defaults.
//
// Per child: the parent keeps maps keyed by the child's segment, `grow`
// (a true ratio, a grown child starting from 0), `basis` (a length along the
// flow), `span` ({cols, rows}, grids and tables), `align_self` and `sticky`
// (the edge a child sticks to while the container scrolls). `set_child`
// changes one child's entries: a name left out stays, null drops it.
//
// A stack (Column, and every container whose body stacks: Container, Card,
// Modal, Sheet, PageSection, Form, Fieldset, Collapsible) draws its
// children through `StackChildren`, so the maps and `divided` read the same
// in all of them.

import type { NodeHandler, Path } from "@nustackdev/ui-core";
import {
	type ComponentType,
	type CSSProperties,
	createContext,
	type ReactNode,
	useContext,
	useLayoutEffect,
	useMemo,
	useState,
} from "react";
import { GAP_CLASSES, PADDING_CLASSES, readStep } from "../../lib/steps";
import { cn } from "../../lib/utils";
import {
	BareCell,
	BlockCell,
	type CellProps,
	FlowProvider,
	NodeChildren,
	useProps,
} from "../../tree";

type Props = Record<string, unknown>;

// ---- lengths ---------------------------------------------------------------

// The page widths, the theme's `--container-*` tokens (theme.css). The theme
// is `inline`, so the tokens are not CSS variables at run time: the values are
// spelled here, and stay in step with theme.css.
const PAGE_WIDTHS: Record<string, string> = {
	form: "30rem",
	prose: "40rem",
	panel: "60rem",
	main: "75rem",
	dashboard: "87.5rem",
	full: "100%",
};
const LENGTH = /^\d+(\.\d+)?(px|rem|em|%|vh|vw|dvh|svh|lvh|ch)$/;

/** A length off the wire as CSS: px for a number, a CSS length, or a page width token. */
export function cssLength(raw: unknown): string | undefined {
	if (typeof raw === "number") return Number.isFinite(raw) && raw >= 0 ? `${raw}px` : undefined;
	if (typeof raw !== "string") return undefined;
	const text = raw.trim();
	if (/^\d+$/.test(text)) return `${text}px`;
	if (text in PAGE_WIDTHS) return PAGE_WIDTHS[text];
	return LENGTH.test(text) ? text : undefined;
}

const SIZE_PROPS = [
	["width", "width"],
	["min_width", "minWidth"],
	["max_width", "maxWidth"],
	["height", "height"],
	["min_height", "minHeight"],
	["max_height", "maxHeight"],
] as const;

/** The style the size props ask for, undefined when none is set. */
export function sizeStyle(props: Props): CSSProperties | undefined {
	let style: CSSProperties | undefined;
	for (const [wire, css] of SIZE_PROPS) {
		const value = cssLength(props[wire]);
		if (value === undefined) continue;
		style ??= {};
		style[css] = value;
	}
	return style;
}

export type Scroll = "y" | "x" | "both";

/**
 * A scrolling box gets min-h-0 / min-w-0 along its scroll axis, so in a
 * flex parent it shrinks to the room it is given and scrolls inside it,
 * instead of growing to its content and pushing the page.
 */
export const SCROLL_CLASSES: Record<Scroll, string> = {
	y: "min-h-0 overflow-y-auto",
	x: "min-w-0 overflow-x-auto",
	both: "min-h-0 min-w-0 overflow-auto",
};

// ---- arrange ---------------------------------------------------------------

/** `justify` on a flex box: the main axis. */
export const JUSTIFY: Record<string, string> = {
	start: "justify-start",
	center: "justify-center",
	end: "justify-end",
	between: "justify-between",
};

/** `align` on a flex box: the cross axis. */
export const ALIGN: Record<string, string> = {
	start: "items-start",
	center: "items-center",
	end: "items-end",
	stretch: "items-stretch",
	baseline: "items-baseline",
};

/** `align_self` for one child. */
export const SELF: Record<string, string> = {
	start: "self-start",
	center: "self-center",
	end: "self-end",
	stretch: "self-stretch",
	baseline: "self-baseline",
};

// ---- the container's own props --------------------------------------------

/** What a container draws when a prop is unset: its own look. */
export type LayoutDefaults = {
	gap?: number;
	padding?: number;
	justify?: string;
	align?: string;
};

export type Layout = {
	/** The gap step, set or the container's default; undefined when it has none. */
	gap: number | undefined;
	/** The padding step when set, else the default; undefined: the container's own pad. */
	padding: number | undefined;
	/** Whether the program set `padding` (a surface's preset pad yields to it). */
	padSet: boolean;
	justify: string;
	align: string;
	divided: boolean;
	/** The size props as a style. */
	size: CSSProperties | undefined;
	/** The scroll class, undefined when nothing scrolls. */
	scroll: string | undefined;
};

/** The layout props off `props`, each unset one taken from `defaults`. */
export function readLayout(props: Props, defaults: LayoutDefaults): Layout {
	const pad = readStep(props.padding);
	const scroll = props.scroll;
	return {
		gap: readStep(props.gap) ?? defaults.gap,
		padding: pad ?? defaults.padding,
		padSet: pad !== undefined,
		justify: typeof props.justify === "string" ? props.justify : (defaults.justify ?? "start"),
		align: typeof props.align === "string" ? props.align : (defaults.align ?? "stretch"),
		divided: props.divided === true,
		size: sizeStyle(props),
		scroll: typeof scroll === "string" ? SCROLL_CLASSES[scroll as Scroll] : undefined,
	};
}

/** `readLayout` for the container at `path`, kept stable while its props stay the same. */
export function useLayout(path: Path, defaults: LayoutDefaults): Layout {
	const props = useProps(path);
	return useMemo(() => readLayout(props, defaults), [props, defaults]);
}

/** The gap class, undefined when there is no gap step. */
export function gapClass(l: Layout): string | undefined {
	return l.gap === undefined ? undefined : GAP_CLASSES[l.gap];
}

/** The padding class, undefined when there is no padding step. */
export function padClass(l: Layout): string | undefined {
	return l.padding === undefined ? undefined : PADDING_CLASSES[l.padding];
}

/** A step as CSS, for a pad a surface keeps in a variable. */
export function stepLength(step: number): string {
	return `calc(var(--spacing) * ${step})`;
}

type Axis = "column" | "row";

/**
 * The classes of a box that stacks children along `axis`: gap, padding
 * (unless `padding` is false: a surface pads itself), justify, align, the
 * hairline between children and the scroll.
 */
export function flowClass(l: Layout, axis: Axis, { padding = true } = {}): string {
	return cn(
		gapClass(l),
		padding && padClass(l),
		JUSTIFY[l.justify] ?? JUSTIFY.start,
		ALIGN[l.align] ?? ALIGN.stretch,
		l.divided &&
			(axis === "column"
				? "divide-y divide-border-subtle [&>*:not(:last-child)]:pb-(--flow-gap)"
				: "divide-x divide-border-subtle [&>*:not(:last-child)]:pr-(--flow-gap)"),
		l.scroll,
	);
}

/** The style a box that stacks children needs: its size, and the gap the hairlines take. */
export function flowStyle(l: Layout): CSSProperties | undefined {
	if (!l.divided) return l.size;
	return { ...l.size, "--flow-gap": stepLength(l.gap ?? 0) } as CSSProperties;
}

// ---- per child maps --------------------------------------------------------

export type Span = { cols: number; rows: number };

export type ChildMaps = {
	grow: Record<string, number>;
	basis: Record<string, string>;
	span: Record<string, Span>;
	alignSelf: Record<string, string>;
	sticky: Record<string, string>;
};

const NONE = {};

function entries(raw: unknown): [string, unknown][] {
	if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return [];
	return Object.entries(raw as Record<string, unknown>);
}

function readMap<T>(raw: unknown, read: (v: unknown) => T | undefined): Record<string, T> {
	let out: Record<string, T> | undefined;
	for (const [key, v] of entries(raw)) {
		const value = read(v);
		if (value === undefined) continue;
		out ??= {};
		out[key] = value;
	}
	return out ?? (NONE as Record<string, T>);
}

/** One `span` entry: whole numbers of at least 1, and not 1 by 1. */
export function readSpan(v: unknown): Span | undefined {
	if (v == null || typeof v !== "object") return undefined;
	const { cols, rows } = v as Record<string, unknown>;
	const c = Math.floor(Number(cols ?? 1));
	const r = Math.floor(Number(rows ?? 1));
	if (!(c >= 1) || !(r >= 1) || (c === 1 && r === 1)) return undefined;
	return { cols: c, rows: r };
}

/** A `span` map off the wire. */
export function readSpans(raw: unknown): Record<string, Span> {
	return readMap(raw, readSpan);
}

const word = (v: unknown) => (typeof v === "string" ? v : undefined);

/** Every per child map off `props`. */
export function readChildMaps(props: Props): ChildMaps {
	return {
		grow: readMap(props.grow, (v) =>
			typeof v === "number" && Number.isFinite(v) && v >= 0 ? v : undefined,
		),
		basis: readMap(props.basis, cssLength),
		span: readSpans(props.span),
		alignSelf: readMap(props.align_self, word),
		sticky: readMap(props.sticky, word),
	};
}

/** The per child maps of the container at `path`, stable while they stay the same. */
export function useChildMaps(path: Path): ChildMaps {
	const props = useProps(path);
	const { grow, basis, span, align_self, sticky } = props;
	return useMemo(
		() => readChildMaps({ grow, basis, span, align_self, sticky }),
		[grow, basis, span, align_self, sticky],
	);
}

const CHILD_MAPS = ["grow", "basis", "span", "align_self", "sticky"] as const;

/**
 * `set_child`: {key, grow?, basis?, span?, align_self?, sticky?} merged into
 * the maps. A name left out keeps its entry; null (or a 1 by 1 span) drops it.
 */
export const setChild: NodeHandler = (ctx, payload) =>
	ctx.update((props) => {
		const p = (payload ?? {}) as Record<string, unknown>;
		const key = p.key == null ? "" : String(p.key);
		if (key === "") return;
		for (const name of CHILD_MAPS) {
			if (!(name in p)) continue;
			const map = { ...(entries(props[name]).length ? (props[name] as Props) : {}) };
			const value = name === "span" ? readSpan(p[name]) : p[name];
			if (value == null) delete map[key];
			else map[key] = value;
			props[name] = map;
		}
	});

/** The handlers every container with per child maps takes. */
export const childHandlers = { set_child: setChild };

/** Where a sticky child sits, by the edge it sticks to. */
export function stickyStyle(side: string | undefined): CSSProperties | undefined {
	if (side !== "top" && side !== "bottom" && side !== "left" && side !== "right") return undefined;
	return { position: "sticky", [side]: 0, zIndex: 1 };
}

// ---- a stack's children ----------------------------------------------------

type StackContextValue = { maps: ChildMaps; Cell: ComponentType<CellProps>; divided: boolean };

const StackContext = createContext<StackContextValue>({
	maps: readChildMaps({}),
	Cell: BlockCell,
	divided: false,
});

// A child the stack lays out (grown, a basis, aligned, sticky) gets a flex
// cell of its own; a divided stack gives every child one, for the hairline.
// Any other child keeps the stack's cell: `BlockCell` when the stack
// stretches, bare otherwise, so `align` places it.
function StackCell({ path, children }: CellProps) {
	const { maps, Cell, divided } = useContext(StackContext);
	const segment = String(path[path.length - 1]);
	const grow = maps.grow[segment];
	const basis = maps.basis[segment];
	const self = maps.alignSelf[segment];
	const sticky = stickyStyle(maps.sticky[segment]);
	const sized = grow !== undefined || basis !== undefined;
	if (!sized && self === undefined && sticky === undefined && !divided) {
		return <Cell path={path}>{children}</Cell>;
	}
	const style: CSSProperties = { ...sticky };
	if (sized) style.flex = `${grow ?? 0} 1 ${basis ?? "0px"}`;
	return (
		<div
			data-slot="stack-cell"
			className={cn("flex min-h-0 min-w-0 flex-col", self && SELF[self], sized && "*:grow")}
			style={style}
		>
			<Cell path={path}>{children}</Cell>
		</div>
	);
}

/**
 * The children of a stack, in a block flow: each in its cell, sized by the
 * stack's per child maps. `skip` leaves out the segments the container
 * places itself (a card's `media`), `order` is a kept order (see ui-core
 * `order.ts`).
 */
export function StackChildren({
	path,
	layout,
	skip,
	order,
}: {
	path: Path;
	layout: Layout;
	skip?: ReadonlySet<string>;
	order?: readonly string[];
}) {
	const maps = useChildMaps(path);
	const Cell = layout.align === "stretch" ? BlockCell : BareCell;
	const value = useMemo(
		() => ({ maps, Cell, divided: layout.divided }),
		[maps, Cell, layout.divided],
	);
	return (
		<FlowProvider flow="block">
			<StackContext.Provider value={value}>
				<NodeChildren path={path} cell={StackCell} indexed skip={skip} order={order} />
			</StackContext.Provider>
		</FlowProvider>
	);
}

/** A box that stacks its children: the classes, the style and the children, for the simple case. */
export function Stack({
	path,
	layout,
	slot,
	className,
	skip,
	order,
	children,
}: {
	path: Path;
	layout: Layout;
	/** The box's `data-slot`, for a container's own part (a section's body). */
	slot?: string;
	className?: string;
	skip?: ReadonlySet<string>;
	order?: readonly string[];
	children?: ReactNode;
}) {
	return (
		<div
			data-slot={slot}
			className={cn("flex min-w-0 flex-col", flowClass(layout, "column"), className)}
			style={flowStyle(layout)}
		>
			{children}
			<StackChildren path={path} layout={layout} skip={skip} order={order} />
		</div>
	);
}

// ---- width ----------------------------------------------------------------

/** The width of `el`, kept current as it resizes; null until measured or when off. */
export function useWidth(el: HTMLElement | null, enabled: boolean): number | null {
	const [width, setWidth] = useState<number | null>(null);
	useLayoutEffect(() => {
		if (!el || !enabled || typeof ResizeObserver === "undefined") return;
		const measure = () => setWidth(el.clientWidth);
		measure();
		const observer = new ResizeObserver(measure);
		observer.observe(el);
		return () => observer.disconnect();
	}, [el, enabled]);
	return enabled ? width : null;
}
