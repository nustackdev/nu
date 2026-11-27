// IconPicker: an icon from a lucide pack or an emoji, searched, picked from a grid.
// Design refs:
//   space-radius.md  §Density Popover (the parts pad, the popover does not)
//   palette.md       text tiers; hover and the current cell on the neutral washes
//   motion.md        Popover (kit PopoverContent)
//   a11y.md          §3 Popover; the grid is one tab stop (a roving tabindex)
//   language/mobile.md  overlays as sheets, 44px taps, no tooltips
//
// The value is a stored icon string ("lucide:folder", "emoji:🌱", "" for
// none; ./icon-picker-model.ts reads and writes it). The picker only says
// which value was picked (`onPick`); what a pick does is the caller's.
//
// Two tabs over one grid, "Emoji" then "Icons" by default (`kinds` picks
// which and in what order). It opens on the first, unless the value is of
// the other kind. The emoji load when the picker first mounts (lazy, a chunk
// of their own); the icons are a pack (./icon-pack.ts, or the caller's).
// Both lead with this browser's recent picks of that kind until there is a
// search. Recent picks are kept under `recentKey` in localStorage, so two
// apps on one origin can keep two lists; null keeps none.
//
// The search box has the caret when it opens. Typing filters by name, group
// and keywords; Enter there takes the first match and Down steps into the
// grid. In the grid the arrows move by cell and by row, Enter or Space picks,
// and Up off the top row goes back to the search. One cell at a time is in the
// tab order, so Tab leaves the grid in one step. `onRemove`, when given, adds
// a "Remove" (or `removeLabel`) button while there is a value.
//
// Three ways to use it: `IconPicker` is the bare panel, `IconPickerContent`
// the panel in a kit `PopoverContent` (the caller owns the `Popover` and its
// trigger or anchor), and `IconPickerField` a whole control, a trigger that
// shows the icon and opens the picker, the way `ColorPicker` is one.
//
// In touch mode the kit Popover is a bottom sheet (./popover.tsx), so the
// picker fills the sheet's width. The grid is sized for the thumb for real:
// 44px cells, as many columns as the sheet's width holds, measured. No
// tooltips (the cell's name stays its accessible name), and the search does
// not take the caret on open, so the on-screen keyboard does not cover the
// grid until the search is tapped.

import type * as React from "react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import { EmptyState } from "./empty-state";
import { IconMark } from "./icon-mark";
import { ICON_PACK, type IconPackGroup } from "./icon-pack";
import {
	type EmojiGroup,
	emojiSections,
	type IconCell,
	type IconKind,
	iconKind,
	loadEmoji,
	normalizeIcon,
	packSections,
	pushRecent,
	RECENT_ICONS_KEY,
	readRecent,
	sectionsFor,
} from "./icon-picker-model";
import { Input } from "./input";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { selectTriggerVariants } from "./select";
import { Spinner } from "./spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

/** Cells per row on desktop: nine 32px cells fill the popover's width. */
export const ICON_PICKER_COLUMNS = 9;

/** A touch cell, px: the thumb's 44, sized for real on a kit-owned surface. */
const TOUCH_CELL = 44;
/** The gap between touch cells, px (`gap-1`). */
const TOUCH_GAP = 4;
/** The sheet's side pad, px, each side (`px-4`). */
const TOUCH_PAD = 16;
/** Columns before the sheet is measured (and in a test, where nothing lays out). */
const TOUCH_COLUMNS = 7;

const KINDS: readonly IconKind[] = ["emoji", "lucide"];

const TAB_LABEL: Record<IconKind, string> = { emoji: "Emoji", lucide: "Icons" };
const SEARCH_LABEL: Record<IconKind, string> = { emoji: "Search emoji", lucide: "Search icons" };

/** The emoji, asked for as the picker mounts, and only when it offers them. */
function useEmoji(wanted: boolean): EmojiGroup[] | "loading" | "failed" {
	const [state, setState] = useState<EmojiGroup[] | "loading" | "failed">("loading");
	useEffect(() => {
		if (!wanted || state !== "loading") return;
		let live = true;
		loadEmoji().then(
			(groups) => live && setState(groups),
			() => live && setState("failed"),
		);
		return () => {
			live = false;
		};
	}, [wanted, state]);
	return state;
}

/** How many touch cells the root's width holds, measured as it changes. */
function useTouchColumns(root: React.RefObject<HTMLDivElement | null>, touch: boolean): number {
	const [columns, setColumns] = useState(TOUCH_COLUMNS);
	useLayoutEffect(() => {
		const el = root.current;
		if (!touch || !el || typeof ResizeObserver === "undefined") return;
		const measure = () => {
			const inner = el.clientWidth - TOUCH_PAD * 2;
			if (inner <= 0) return;
			setColumns(Math.max(1, Math.floor((inner + TOUCH_GAP) / (TOUCH_CELL + TOUCH_GAP))));
		};
		measure();
		const watch = new ResizeObserver(measure);
		watch.observe(el);
		return () => watch.disconnect();
	}, [root, touch]);
	return touch ? columns : ICON_PICKER_COLUMNS;
}

export interface IconPickerProps {
	/** The icon now, as stored ("" for none). Marked in the grid. */
	value: string;
	/** A cell was picked: its stored value. */
	onPick: (value: string) => void;
	/** Clear the icon. Unset, there is no remove button. */
	onRemove?: () => void;
	/** The remove button's text. */
	removeLabel?: string;
	/** Which tabs, in order. The picker opens on the first unless `value` is of another. */
	kinds?: readonly IconKind[];
	/** The icons the Icons tab offers, in groups. The kit's pack when unset. */
	pack?: readonly IconPackGroup[];
	/** The localStorage key recent picks are kept under; null keeps none. */
	recentKey?: string | null;
	className?: string;
}

function IconPicker({
	value,
	onPick,
	onRemove,
	removeLabel = "Remove",
	kinds = KINDS,
	pack = ICON_PACK,
	recentKey = RECENT_ICONS_KEY,
	className,
}: IconPickerProps) {
	const touch = useTouch();
	const current = normalizeIcon(value);
	const offered = kinds.length > 0 ? kinds : KINDS;
	const [tab, setTab] = useState<IconKind>(() => {
		const kind = iconKind(current);
		return kind && offered.includes(kind) ? kind : offered[0];
	});
	const [query, setQuery] = useState("");
	const [active, setActive] = useState(0);
	const [recent] = useState(() => (recentKey ? readRecent(recentKey) : []));
	const emoji = useEmoji(offered.includes("emoji"));
	const rootRef = useRef<HTMLDivElement | null>(null);
	const columns = useTouchColumns(rootRef, touch);
	const icons = useMemo(() => packSections(pack), [pack]);
	const emojis = useMemo(() => (Array.isArray(emoji) ? emojiSections(emoji) : []), [emoji]);

	const sections = useMemo(
		() =>
			sectionsFor(
				tab === "lucide" ? icons : emojis,
				recent.filter((v) => iconKind(v) === tab),
				query,
			),
		[tab, icons, emojis, recent, query],
	);

	// The grid as rows of flat cell indices, so the arrows can move by row
	// across a group's short last row.
	const { cells, rows, place } = useMemo(() => {
		const cells: IconCell[] = [];
		const rows: number[][] = [];
		const place: [row: number, col: number][] = [];
		for (const s of sections) {
			for (let i = 0; i < s.cells.length; i += columns) {
				const row: number[] = [];
				for (const cell of s.cells.slice(i, i + columns)) {
					place.push([rows.length, row.length]);
					row.push(cells.length);
					cells.push(cell);
				}
				rows.push(row);
			}
		}
		return { cells, rows, place };
	}, [sections, columns]);

	// A new search or tab starts the grid over, at its top.
	// biome-ignore lint/correctness/useExhaustiveDependencies: the reset is what the query and tab change mean.
	useEffect(() => {
		setActive(0);
		const body = rootRef.current?.querySelector("[data-slot=icon-picker-body]");
		if (body) body.scrollTop = 0;
	}, [query, tab]);

	// The caret starts in the search, before the popover's own focus pass, so
	// that pass finds focus already inside and leaves it be. Not on touch: the
	// on-screen keyboard would cover the grid before anyone asked for it.
	// biome-ignore lint/correctness/useExhaustiveDependencies: once, on open.
	useEffect(() => {
		if (!touch) rootRef.current?.querySelector<HTMLInputElement>("input")?.focus();
	}, []);

	const pick = useCallback(
		(cell: IconCell) => {
			if (recentKey) pushRecent(recentKey, cell.value);
			onPick(cell.value);
		},
		[onPick, recentKey],
	);

	const focusCell = (i: number) => {
		setActive(i);
		rootRef.current?.querySelector<HTMLElement>(`[data-cell="${i}"]`)?.focus();
	};

	const focusSearch = () => rootRef.current?.querySelector<HTMLInputElement>("input")?.focus();

	const onSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.nativeEvent.isComposing) return;
		if (e.key === "ArrowDown" && cells.length > 0) {
			e.preventDefault();
			focusCell(Math.min(active, cells.length - 1));
		} else if (e.key === "Enter" && cells.length > 0) {
			e.preventDefault();
			pick(cells[0]);
		}
	};

	const onGridKey = (e: React.KeyboardEvent<HTMLDivElement>) => {
		const at = place[active];
		if (!at) return;
		const [r, c] = at;
		const inRow = (row: number[] | undefined) => (row ? row[Math.min(c, row.length - 1)] : -1);
		let next = -1;
		if (e.key === "ArrowRight") next = active + 1 < cells.length ? active + 1 : active;
		else if (e.key === "ArrowLeft") next = active > 0 ? active - 1 : active;
		else if (e.key === "ArrowDown") next = r + 1 < rows.length ? inRow(rows[r + 1]) : active;
		else if (e.key === "ArrowUp") {
			e.preventDefault();
			if (r === 0) focusSearch();
			else focusCell(inRow(rows[r - 1]));
			return;
		} else if (e.key === "Home") next = 0;
		else if (e.key === "End") next = cells.length - 1;
		else return;
		e.preventDefault();
		focusCell(next);
	};

	const pad = touch ? "px-4" : "px-2";
	const grid = { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` };

	const body = () => {
		if (tab === "emoji" && emoji === "loading") {
			return <EmptyState icon={<Spinner size="sm" tone="neutral" label="Loading emoji" />} />;
		}
		if (tab === "emoji" && emoji === "failed") {
			return <EmptyState size="sm">Emoji could not load</EmptyState>;
		}
		if (cells.length === 0) return <EmptyState size="sm">Nothing matches</EmptyState>;
		let base = 0;
		return (
			// biome-ignore lint/a11y/noStaticElementInteractions: the arrows land here from the cells, which are real buttons
			<div onKeyDown={onGridKey}>
				{sections.map((s) => {
					const start = base;
					base += s.cells.length;
					const groupRows: IconCell[][] = [];
					for (let i = 0; i < s.cells.length; i += columns) {
						groupRows.push(s.cells.slice(i, i + columns));
					}
					return (
						<section key={s.label} aria-label={s.label}>
							<h3 className="select-none px-1 pt-2 pb-1 text-xs text-text-muted">{s.label}</h3>
							{groupRows.map((row, ri) => (
								<div
									key={row[0].value}
									className={cn("grid justify-items-center", touch ? "gap-1" : "gap-0.5")}
									style={grid}
								>
									{row.map((cell, ci) => {
										const i = start + ri * columns + ci;
										const on = cell.value === current;
										return (
											<button
												key={cell.value}
												type="button"
												data-slot="icon-picker-cell"
												data-cell={i}
												tabIndex={i === active ? 0 : -1}
												aria-label={cell.label}
												aria-pressed={on}
												title={touch ? undefined : cell.label}
												className={cn(
													"flex cursor-default items-center justify-center rounded-md text-text-secondary",
													"transition-colors duration-fast ease-out",
													"hover:bg-bg-hover hover:text-text-primary active:bg-bg-press",
													"focus-visible:bg-bg-press focus-visible:text-text-primary focus-visible:outline-hidden",
													"focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring",
													touch ? "h-tap w-full" : "size-8",
													on && "bg-bg-press text-text-primary",
												)}
												onFocus={() => setActive(i)}
												onClick={() => pick(cell)}
											>
												<IconMark icon={cell.icon} size="md" />
											</button>
										);
									})}
								</div>
							))}
						</section>
					);
				})}
			</div>
		);
	};

	return (
		<div ref={rootRef} data-slot="icon-picker" className={cn("flex flex-col", className)}>
			<Tabs value={tab} onValueChange={(v) => setTab(v as IconKind)} className="gap-0">
				<div className={cn("flex min-h-7 items-center justify-between gap-2 pt-1", pad)}>
					{offered.length > 1 ? (
						<TabsList variant="line" className="border-b-0">
							{offered.map((k) => (
								<TabsTrigger key={k} value={k} size={touch ? "md" : "sm"}>
									{TAB_LABEL[k]}
								</TabsTrigger>
							))}
						</TabsList>
					) : (
						<span />
					)}
					{onRemove && current ? (
						<Button variant="ghost" size={touch ? "md" : "sm"} onClick={onRemove}>
							{removeLabel}
						</Button>
					) : null}
				</div>
				<div className={cn("pt-2 pb-1", pad)}>
					<Input
						// Touch: the sheet is the kit's own, so its search is a thumb's size.
						size={touch ? "lg" : "sm"}
						type="search"
						aria-label={SEARCH_LABEL[tab]}
						placeholder={SEARCH_LABEL[tab]}
						value={query}
						onChange={(e) => setQuery(e.currentTarget.value)}
						onKeyDown={onSearchKey}
					/>
				</div>
				{offered.map((k) => (
					<TabsContent
						key={k}
						value={k}
						tabIndex={-1}
						data-slot="icon-picker-body"
						className={cn(
							"overflow-x-hidden overflow-y-auto overscroll-contain pb-2",
							touch ? "h-[50dvh]" : "h-72",
							pad,
						)}
					>
						{tab === k ? body() : null}
					</TabsContent>
				))}
			</Tabs>
		</div>
	);
}

export type IconPickerContentProps = IconPickerProps &
	Omit<React.ComponentProps<typeof PopoverContent>, "children" | "className">;

/**
 * The picker in a kit popover (a bottom sheet on touch). Put it inside a
 * `Popover` whose trigger or anchor is the icon being changed.
 */
function IconPickerContent({
	value,
	onPick,
	onRemove,
	removeLabel,
	kinds,
	pack,
	recentKey,
	className,
	"aria-label": ariaLabel = "Choose an icon",
	...content
}: IconPickerContentProps) {
	const touch = useTouch();
	return (
		<PopoverContent
			// The sheet keeps its own slot in touch mode (its motion keys on it).
			{...(touch ? {} : { "data-slot": "icon-picker-content" })}
			aria-label={ariaLabel}
			className={cn("flex flex-col p-0", !touch && "w-82")}
			{...content}
		>
			<IconPicker
				value={value}
				onPick={onPick}
				onRemove={onRemove}
				removeLabel={removeLabel}
				kinds={kinds}
				pack={pack}
				recentKey={recentKey}
				className={className}
			/>
		</PopoverContent>
	);
}

type Size = "sm" | "md" | "lg";
type Variant = "default" | "ghost" | "filled";

const markSizes = { sm: "sm", md: "sm", lg: "md" } as const;

export interface IconPickerFieldProps
	extends Pick<IconPickerProps, "kinds" | "pack" | "recentKey" | "removeLabel"> {
	/** The icon, as stored ("" for none). */
	value?: string;
	defaultValue?: string;
	/** A pick, or "" from the remove button. */
	onValueChange?: (value: string) => void;
	/** Offer a remove button while there is an icon. */
	clearable?: boolean;
	/** What the trigger says while there is no icon. */
	placeholder?: string;
	variant?: Variant;
	size?: Size;
	invalid?: boolean;
	disabled?: boolean;
	className?: string;
	id?: string;
	"aria-label"?: string;
	/** More props for the trigger button (aria, a key handler, autofocus). */
	triggerProps?: React.ComponentProps<"button">;
}

/**
 * A whole icon control: a trigger that shows the icon (or the placeholder)
 * and opens the picker. A pick lands and closes it.
 */
function IconPickerField({
	value: valueProp,
	defaultValue = "",
	onValueChange,
	clearable = true,
	placeholder = "No icon",
	variant,
	size = "md",
	invalid,
	disabled,
	className,
	id,
	"aria-label": ariaLabel,
	triggerProps,
	kinds,
	pack,
	recentKey,
	removeLabel,
}: IconPickerFieldProps) {
	const [internal, setInternal] = useState(() => normalizeIcon(defaultValue));
	const value = valueProp === undefined ? internal : normalizeIcon(valueProp);
	const [open, setOpen] = useState(false);
	const land = (next: string) => {
		if (valueProp === undefined) setInternal(next);
		if (next !== value) onValueChange?.(next);
		setOpen(false);
	};
	return (
		<Popover open={open} onOpenChange={setOpen}>
			<PopoverTrigger
				{...triggerProps}
				data-slot="icon-picker-trigger"
				disabled={disabled}
				id={id}
				aria-label={ariaLabel}
				aria-invalid={invalid || undefined}
				data-placeholder={value ? undefined : ""}
				className={cn(
					selectTriggerVariants({ variant, size, invalid }),
					"w-auto justify-start",
					className,
				)}
			>
				{/* A box of its own: the trigger truncates a span and sizes an svg, the mark is neither's. */}
				<span className="flex items-center">
					{value ? <IconMark icon={value} size={markSizes[size]} /> : placeholder}
				</span>
			</PopoverTrigger>
			<IconPickerContent
				align="start"
				value={value}
				onPick={land}
				onRemove={clearable ? () => land("") : undefined}
				removeLabel={removeLabel}
				kinds={kinds}
				pack={pack}
				recentKey={recentKey}
			/>
		</Popover>
	);
}

export { IconPicker, IconPickerContent, IconPickerField };
