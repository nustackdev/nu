// ColorPicker: a swatch trigger that opens a Popover with a saturation and
// brightness area, a hue slider, a hex field and an optional swatch row.
//
// The value is a `#rrggbb` string. `onValueChange` hears every move (a drag,
// a valid hex as it is typed), `onValueCommit` the end of one (a release, an
// arrow key, a swatch, the hex field's blur or Enter), the way the kit Slider
// splits them. Enter in the hex field also calls `onEnter` with the trigger,
// so a caller can submit the Form the trigger sits in (the popover is
// portalled out of it), and closes the popover.
//
// `swatches` is a list of hex strings, or "palette" for the kit's chart
// palette, read off the tokens where the trigger sits (lib/chart/theme.ts),
// so a swatch row follows the theme it opens in.
//
// Design refs:
//   space-radius.md  §Popover (pad 12, radius md)
//   motion.md        Popover (kit PopoverContent), Slider thumb
//   a11y.md          §3 Popover, Slider keys; the area is a 2D slider:
//                    arrows move one step, Shift+arrow ten.

import * as React from "react";

import { readChartTokens } from "../../lib/chart/theme";
import { cn } from "../../lib/utils";
import { Input } from "./input";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { selectTriggerVariants } from "./select";
import { Slider } from "./slider";

type Size = "sm" | "md" | "lg";
type Variant = "default" | "ghost" | "filled";

// ---- color math ------------------------------------------------------------

/** `#rgb`, `#rrggbb`, with or without the `#`, as lowercase `#rrggbb`; null if not hex. */
export function normalizeHex(raw: unknown): string | null {
	if (typeof raw !== "string") return null;
	const s = raw.trim().replace(/^#/, "").toLowerCase();
	if (/^[0-9a-f]{6}$/.test(s)) return `#${s}`;
	if (/^[0-9a-f]{3}$/.test(s)) return `#${s[0]}${s[0]}${s[1]}${s[1]}${s[2]}${s[2]}`;
	return null;
}

export type Hsv = { h: number; s: number; v: number };

export function hexToHsv(hex: string): Hsv {
	const n = Number.parseInt((normalizeHex(hex) ?? "#000000").slice(1), 16);
	const r = ((n >> 16) & 255) / 255;
	const g = ((n >> 8) & 255) / 255;
	const b = (n & 255) / 255;
	const max = Math.max(r, g, b);
	const d = max - Math.min(r, g, b);
	let h = 0;
	if (d) {
		if (max === r) h = ((g - b) / d) % 6;
		else if (max === g) h = (b - r) / d + 2;
		else h = (r - g) / d + 4;
	}
	return { h: (h * 60 + 360) % 360, s: max ? (d / max) * 100 : 0, v: max * 100 };
}

export function hsvToHex({ h, s, v }: Hsv): string {
	const sat = s / 100;
	const val = v / 100;
	const f = (k: number) => {
		const x = (k + h / 60) % 6;
		const c = val - val * sat * Math.max(0, Math.min(x, 4 - x, 1));
		return Math.round(c * 255)
			.toString(16)
			.padStart(2, "0");
	};
	return `#${f(5)}${f(3)}${f(1)}`;
}

const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n));

function paletteAt(el: Element | null): string[] {
	const tokens = readChartTokens(el ?? document.documentElement).palette;
	return tokens.map(normalizeHex).filter((x): x is string => x !== null);
}

// ---- the saturation / brightness area -------------------------------------

function ColorArea({
	hsv,
	disabled,
	onMove,
	onCommit,
}: {
	hsv: Hsv;
	disabled?: boolean;
	onMove: (next: Hsv) => void;
	onCommit: () => void;
}) {
	const box = React.useRef<HTMLDivElement>(null);

	const at = (e: React.PointerEvent) => {
		const r = box.current?.getBoundingClientRect();
		if (!r?.width || !r.height) return;
		onMove({
			h: hsv.h,
			s: clamp(((e.clientX - r.left) / r.width) * 100, 0, 100),
			v: clamp(100 - ((e.clientY - r.top) / r.height) * 100, 0, 100),
		});
	};

	const onKeyDown = (e: React.KeyboardEvent) => {
		const by = e.shiftKey ? 10 : 1;
		const moves: Record<string, [number, number]> = {
			ArrowLeft: [-by, 0],
			ArrowRight: [by, 0],
			ArrowUp: [0, by],
			ArrowDown: [0, -by],
		};
		const move = moves[e.key];
		if (!move) return;
		e.preventDefault();
		onMove({ h: hsv.h, s: clamp(hsv.s + move[0], 0, 100), v: clamp(hsv.v + move[1], 0, 100) });
		onCommit();
	};

	const s = Math.round(hsv.s);
	const v = Math.round(hsv.v);
	return (
		<div
			ref={box}
			data-slot="color-picker-area"
			className="relative h-32 w-full touch-none rounded-sm"
			style={{
				backgroundColor: `hsl(${hsv.h} 100% 50%)`,
				backgroundImage:
					"linear-gradient(to top, #000, transparent), linear-gradient(to right, #fff, transparent)",
			}}
			onPointerDown={(e) => {
				if (disabled) return;
				e.currentTarget.setPointerCapture?.(e.pointerId);
				box.current?.querySelector<HTMLElement>("[role=slider]")?.focus();
				at(e);
			}}
			onPointerMove={(e) => {
				if (e.currentTarget.hasPointerCapture?.(e.pointerId)) at(e);
			}}
			onPointerUp={(e) => {
				if (!e.currentTarget.hasPointerCapture?.(e.pointerId)) return;
				e.currentTarget.releasePointerCapture(e.pointerId);
				onCommit();
			}}
		>
			<div
				role="slider"
				tabIndex={disabled ? -1 : 0}
				aria-label="Saturation and brightness"
				aria-valuemin={0}
				aria-valuemax={100}
				aria-valuenow={s}
				aria-valuetext={`Saturation ${s}%, brightness ${v}%`}
				aria-disabled={disabled || undefined}
				onKeyDown={onKeyDown}
				data-slot="color-picker-area-thumb"
				className={cn(
					"absolute size-3.5 -translate-x-1/2 translate-y-1/2 rounded-full",
					"border-2 border-white shadow-[0_0_0_1px_rgb(0_0_0/0.35)]",
					"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-elevated",
				)}
				style={{ left: `${hsv.s}%`, bottom: `${hsv.v}%` }}
			/>
		</div>
	);
}

// ---- the picker ------------------------------------------------------------

export interface ColorPickerProps {
	/** `#rrggbb`. */
	value?: string;
	defaultValue?: string;
	/** Every move: a drag, a valid hex as it is typed. */
	onValueChange?: (value: string) => void;
	/** The end of a move: a release, an arrow key, a swatch, the hex field's blur or Enter. */
	onValueCommit?: (value: string) => void;
	/** Enter in the hex field with a valid hex, after it landed. Gets the trigger. */
	onEnter?: (trigger: HTMLButtonElement | null) => void;
	/** Preset colors, or "palette" for the kit chart palette. */
	swatches?: string[] | "palette";
	/** Show the hex next to the swatch on the trigger. */
	showHex?: boolean;
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

const swatchSizes = { sm: "size-3.5", md: "size-4", lg: "size-4" } as const;

function ColorPicker({
	value: valueProp,
	defaultValue = "#000000",
	onValueChange,
	onValueCommit,
	onEnter,
	swatches,
	showHex = true,
	variant,
	size = "md",
	invalid,
	disabled,
	className,
	id,
	"aria-label": ariaLabel,
	triggerProps,
}: ColorPickerProps) {
	const [internal, setInternal] = React.useState(normalizeHex(defaultValue) ?? "#000000");
	const value = valueProp === undefined ? internal : (normalizeHex(valueProp) ?? "#000000");
	const [open, setOpen] = React.useState(false);
	const trigger = React.useRef<HTMLButtonElement>(null);

	// Hue and saturation are kept apart from the hex: at black or grey the hex
	// forgets them, and the area and hue thumb should stay where they were.
	// `synced` is the value `hsv` and the hex field were last brought in line
	// with; a value from outside (a write, a reset) moves them, our own moves
	// arrive already in line.
	const [hsv, setHsv] = React.useState<Hsv>(() => hexToHsv(value));
	const [draft, setDraft] = React.useState(value);
	const [synced, setSynced] = React.useState(value);
	if (synced !== value) {
		setSynced(value);
		setDraft(value);
		if (hsvToHex(hsv) !== value) {
			const next = hexToHsv(value);
			setHsv(next.s === 0 || next.v === 0 ? { ...next, h: hsv.h } : next);
		}
	}

	const [palette, setPalette] = React.useState<string[]>([]);
	const list = swatches === "palette" ? palette : (swatches ?? []).map(normalizeHex);

	// The value as of the last move, ahead of the render it causes: the kit
	// Slider reports a key's commit in the same tick as the move.
	const latest = React.useRef(value);
	latest.current = value;
	const change = (next: string) => {
		latest.current = next;
		if (valueProp === undefined) setInternal(next);
		onValueChange?.(next);
	};
	const commit = (next: string = latest.current) => onValueCommit?.(next);

	const move = (next: Hsv) => {
		const hex = hsvToHex(next);
		setHsv(next);
		setSynced(hex);
		setDraft(hex);
		change(hex);
	};

	const draftHex = normalizeHex(draft);
	const swatchSize = swatchSizes[size];

	return (
		<Popover
			open={open}
			onOpenChange={(next) => {
				if (next && swatches === "palette") setPalette(paletteAt(trigger.current));
				// Closing ends whatever was in flight (a typed hex, then Esc).
				if (!next) commit();
				setOpen(next);
			}}
		>
			<PopoverTrigger
				{...triggerProps}
				ref={trigger}
				data-slot="color-picker-trigger"
				disabled={disabled}
				id={id}
				aria-label={ariaLabel}
				aria-invalid={invalid || undefined}
				className={cn(
					selectTriggerVariants({ variant, size, invalid }),
					"justify-start",
					className,
				)}
			>
				<span
					data-slot="color-picker-swatch"
					aria-hidden
					className={cn("shrink-0 rounded-sm border border-border-default", swatchSize)}
					style={{ backgroundColor: value }}
				/>
				{showHex && <span className="font-mono tabular-nums">{value}</span>}
			</PopoverTrigger>
			<PopoverContent
				data-slot="color-picker-content"
				align="start"
				className="flex w-60 flex-col gap-3"
			>
				<ColorArea hsv={hsv} disabled={disabled} onMove={move} onCommit={() => commit()} />
				<Slider
					size="sm"
					min={0}
					max={359}
					step={1}
					value={[Math.round(hsv.h)]}
					thumbLabels={["Hue"]}
					disabled={disabled}
					onValueChange={([h]) => move({ ...hsv, h: h ?? 0 })}
					onValueCommit={([h]) => commit(hsvToHex({ ...hsv, h: h ?? 0 }))}
					className={cn(
						"[&_[data-slot=slider-track]]:h-2.5!",
						"[&_[data-slot=slider-track]]:bg-[linear-gradient(to_right,#f00,#ff0,#0f0,#0ff,#00f,#f0f,#f00)]",
						"[&_[data-slot=slider-range]]:bg-transparent",
					)}
				/>
				<div className="flex items-center gap-2">
					<span
						aria-hidden
						className="size-6 shrink-0 rounded-sm border border-border-default"
						style={{ backgroundColor: value }}
					/>
					<Input
						data-slot="color-picker-hex"
						aria-label="Hex color"
						size="sm"
						className="font-mono"
						spellCheck={false}
						autoComplete="off"
						maxLength={7}
						disabled={disabled}
						invalid={draftHex === null}
						value={draft}
						onChange={(e) => {
							// A full six digits lands as it is typed; `#abc` waits for
							// blur or Enter, or it would expand under the caret.
							const text = e.target.value;
							setDraft(text);
							const hex = /^#?[0-9a-f]{6}$/i.test(text.trim()) ? normalizeHex(text) : null;
							if (hex && hex !== value) {
								const next = hexToHsv(hex);
								setHsv(next.s === 0 || next.v === 0 ? { ...next, h: hsv.h } : next);
								setSynced(hex);
								change(hex);
							}
						}}
						onBlur={() => {
							if (draftHex && draftHex !== value) change(draftHex);
							if (draftHex) commit(draftHex);
							setDraft(draftHex ?? value);
						}}
						onKeyDown={(e) => {
							if (e.key !== "Enter" || e.nativeEvent.isComposing || e.keyCode === 229) return;
							e.preventDefault();
							if (!draftHex) return;
							if (draftHex !== value) change(draftHex);
							setDraft(draftHex);
							commit(draftHex);
							onEnter?.(trigger.current);
							setOpen(false);
						}}
					/>
				</div>
				{list.length > 0 && (
					<div data-slot="color-picker-swatches" className="flex flex-wrap gap-1.5">
						{list.map((hex, i) =>
							hex ? (
								<button
									// biome-ignore lint/suspicious/noArrayIndexKey: a preset list may repeat a color.
									key={i}
									type="button"
									aria-label={hex}
									aria-pressed={hex === value}
									disabled={disabled}
									onClick={() => {
										if (hex !== value) change(hex);
										commit(hex);
									}}
									className={cn(
										"size-5 rounded-sm border border-border-default cursor-default",
										"transition-transform duration-fast ease-out hover:scale-110",
										"focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-elevated",
										"aria-pressed:ring-2 aria-pressed:ring-accent aria-pressed:ring-offset-1 aria-pressed:ring-offset-bg-elevated",
									)}
									style={{ backgroundColor: hex }}
								/>
							) : null,
						)}
					</div>
				)}
			</PopoverContent>
		</Popover>
	);
}

export { ColorPicker };
