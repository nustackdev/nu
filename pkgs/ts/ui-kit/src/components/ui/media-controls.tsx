// The media transport: the pieces a player is built from, and the one bar
// that puts them in a row.
//
// Every piece reads the `MediaApi` that lib/media `useMedia` hands back, so a
// piece knows nothing of the element it drives and a story can pass a fake.
// Video lays out `MediaControls` over its frame; Audio places the same pieces
// in one dense row with a waveform for a track.
//
// The scrub bar is its own slider rather than the kit Slider: it draws a
// buffered run and a hover time under the pointer, and takes any track the
// player draws (a waveform). It keeps slider semantics: role, a time in words
// for `aria-valuetext`, arrows, page keys, home and end.
//
// In touch mode (../../lib/touch.ts) the pieces keep their look and size; a
// finger gets a 44px tap area on each, the scrub thumb always shows (there is
// no hover to bring it up), and volume is the mute button alone: a phone sets
// the level with its own buttons, and iOS does not let a page set it at all.
// The speed menu opens as a sheet, as every kit menu does. The players keep
// their bar up the whole time in touch mode.

import {
	Download,
	Maximize,
	Minimize,
	Pause,
	Play,
	RotateCcw,
	Volume1,
	Volume2,
	VolumeX,
} from "lucide-react";
import * as React from "react";
import {
	clampTime,
	formatRate,
	formatTime,
	fractionOf,
	knownDuration,
	RATES,
	SEEK_STEP,
	SEEK_STEP_BIG,
	spokenTime,
	timeAt,
} from "../../lib/media/model";
import type { MediaApi } from "../../lib/media/use-media";
import { useTouch } from "../../lib/touch";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuLabel,
	DropdownMenuRadioGroup,
	DropdownMenuRadioItem,
	DropdownMenuTrigger,
} from "./dropdown-menu";
import { IconButton, type IconButtonProps } from "./icon-button";
import { Kbd } from "./kbd";
import { Popover, PopoverAnchor, PopoverContent } from "./popover";
import { Slider } from "./slider";
import { TooltipProvider } from "./tooltip";

/** A control's tooltip: what it does and the key that does it too. */
function tip(label: string, key: string) {
	return (
		<span className="flex items-center gap-2">
			{label}
			<Kbd variant="ghost" size="sm">
				{key}
			</Kbd>
		</span>
	);
}

// ---------------------------------------------------------------------------
// Scrubber

/** Where the track drawing sits: both fractions of the whole, in [0, 1]. */
export interface ScrubTrackState {
	played: number;
	buffered: number;
	/** Under the pointer, or null when it is elsewhere. */
	hover: number | null;
}

export interface ScrubberProps
	extends Omit<React.ComponentProps<"div">, "children" | "onChange" | "role"> {
	time: number;
	duration: number;
	/** Where the loaded run ends, in seconds. */
	buffered?: number;
	onSeek: (t: number) => void;
	/** The accessible name. */
	label?: string;
	/** Draws the track; the plain bar when left out. */
	children?: (state: ScrubTrackState) => React.ReactNode;
}

export function Scrubber({
	time,
	duration,
	buffered = 0,
	onSeek,
	label = "Seek",
	children,
	className,
	...props
}: ScrubberProps) {
	const touch = useTouch();
	const box = React.useRef<HTMLDivElement>(null);
	const [hover, setHover] = React.useState<number | null>(null);
	// While dragging, the bar follows the pointer, not the element: a seek can
	// take a moment to land and the bar must not lag behind the hand.
	const [drag, setDrag] = React.useState<number | null>(null);
	const live = knownDuration(duration);

	const at = (clientX: number) => {
		const r = box.current?.getBoundingClientRect();
		if (!r || r.width === 0) return 0;
		return Math.min(1, Math.max(0, (clientX - r.left) / r.width));
	};

	const played = drag ?? fractionOf(time, duration);
	const shown = drag ?? hover;

	const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
		props.onKeyDown?.(e);
		if (e.defaultPrevented || !live || e.altKey || e.ctrlKey || e.metaKey) return;
		const step = e.shiftKey ? SEEK_STEP_BIG : SEEK_STEP;
		const by: Record<string, number> = {
			ArrowRight: step,
			ArrowUp: step,
			ArrowLeft: -step,
			ArrowDown: -step,
			PageUp: SEEK_STEP_BIG,
			PageDown: -SEEK_STEP_BIG,
		};
		let to: number | null = null;
		if (e.key in by) to = clampTime(time + by[e.key], duration);
		else if (e.key === "Home") to = 0;
		else if (e.key === "End") to = duration;
		if (to === null) return;
		e.preventDefault();
		onSeek(to);
	};

	return (
		<div
			ref={box}
			role="slider"
			tabIndex={live ? 0 : -1}
			aria-label={label}
			aria-orientation="horizontal"
			aria-valuemin={0}
			aria-valuemax={live ? Math.round(duration) : 0}
			aria-valuenow={Math.round(live ? clampTime(time, duration) : 0)}
			aria-valuetext={live ? `${spokenTime(time)} of ${spokenTime(duration)}` : "unknown"}
			aria-disabled={live ? undefined : true}
			data-slot="scrubber"
			data-dragging={drag !== null ? "" : undefined}
			{...props}
			className={cn(
				"group/scrub relative flex h-4 w-full touch-none select-none items-center rounded-sm",
				// Touch: a 44px tall tap area; the buttons under it come later and win.
				"nu-tap",
				"cursor-default outline-hidden",
				"focus-visible:ring-2 focus-visible:ring-ring",
				!live && "pointer-events-none",
				className,
			)}
			onKeyDown={onKeyDown}
			onPointerDown={(e) => {
				props.onPointerDown?.(e);
				if (!live || e.button !== 0) return;
				e.currentTarget.setPointerCapture(e.pointerId);
				const f = at(e.clientX);
				setDrag(f);
				onSeek(timeAt(f, duration));
			}}
			onPointerMove={(e) => {
				props.onPointerMove?.(e);
				const f = at(e.clientX);
				if (e.pointerType === "mouse") setHover(f);
				if (drag !== null) {
					setDrag(f);
					onSeek(timeAt(f, duration));
				}
			}}
			onPointerUp={(e) => {
				props.onPointerUp?.(e);
				setDrag(null);
			}}
			onPointerCancel={() => setDrag(null)}
			onPointerLeave={(e) => {
				props.onPointerLeave?.(e);
				setHover(null);
			}}
		>
			{children ? (
				children({ played, buffered: fractionOf(buffered, duration), hover: shown })
			) : (
				<ScrubBar played={played} buffered={fractionOf(buffered, duration)} thumb={touch} />
			)}
			{shown !== null && live ? (
				<span
					aria-hidden="true"
					data-slot="scrubber-time"
					className={cn(
						"pointer-events-none absolute bottom-full mb-1.5 -translate-x-1/2 rounded-sm px-1.5 py-0.5",
						"border border-border-default bg-bg-elevated shadow-floating",
						"font-mono text-xs leading-tight tabular-nums text-text-primary",
					)}
					style={{ left: `clamp(1.25rem, ${shown * 100}%, calc(100% - 1.25rem))` }}
				>
					{formatTime(timeAt(shown, duration), duration)}
				</span>
			) : null}
		</div>
	);
}

/** The plain scrub track: loaded run, played run, and a thumb on hover, focus or drag (always, with `thumb`). */
function ScrubBar({
	played,
	buffered,
	thumb = false,
}: {
	played: number;
	buffered: number;
	thumb?: boolean;
}) {
	return (
		<>
			<span className="relative h-1 w-full overflow-hidden rounded-full bg-bg-press">
				<span
					className="absolute inset-y-0 left-0 bg-bg-press-strong"
					style={{ width: `${Math.max(played, buffered) * 100}%` }}
				/>
				<span
					className="absolute inset-y-0 left-0 bg-accent"
					style={{ width: `${played * 100}%` }}
				/>
			</span>
			<span
				aria-hidden="true"
				className={cn(
					"pointer-events-none absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent",
					"opacity-0 transition-opacity duration-fast ease-out",
					"group-hover/scrub:opacity-100 group-focus-visible/scrub:opacity-100 group-data-[dragging]/scrub:opacity-100",
					thumb && "opacity-100",
				)}
				style={{ left: `${played * 100}%` }}
			/>
		</>
	);
}

// ---------------------------------------------------------------------------
// Buttons and readouts

export function MediaPlayButton({
	media,
	variant = "ghost",
	size = "sm",
	...props
}: { media: MediaApi } & Omit<IconButtonProps, "aria-label" | "onClick">) {
	const label = media.playing ? "Pause" : media.ended ? "Replay" : "Play";
	const Glyph = media.playing ? Pause : media.ended ? RotateCcw : Play;
	return (
		<IconButton
			variant={variant}
			size={size}
			aria-label={label}
			tip={tip(label, "K")}
			tipSide="top"
			disabled={media.error}
			onClick={media.toggle}
			data-slot="media-play"
			{...props}
		>
			<Glyph className={cn(!media.ended && "fill-current")} />
		</IconButton>
	);
}

/** `0:12 / 3:45`, mono and tabular so the digits never jitter. */
export function MediaTime({
	time,
	duration,
	className,
	...props
}: { time: number; duration: number } & React.ComponentProps<"span">) {
	return (
		<span
			data-slot="media-time"
			className={cn(
				"whitespace-nowrap font-mono text-xs tabular-nums text-text-secondary",
				className,
			)}
			{...props}
		>
			<span className="text-text-primary">{formatTime(time, duration)}</span>
			<span className="text-text-muted"> / </span>
			{knownDuration(duration) ? formatTime(duration) : "--:--"}
		</span>
	);
}

/**
 * How long the volume panel stays after the pointer leaves the button or the
 * panel: time to cross the gap between them.
 */
const VOLUME_CLOSE_MS = 150;

/**
 * Mute, and the level in a panel that floats above it on hover or keyboard
 * focus: there when you reach for it, out of the way otherwise, and never
 * moving the row. A click on the button still mutes; the panel does not trap
 * focus, Tab goes from the button into the slider and on out of it.
 *
 * The panel portals into the control's own box, so it sits right after the
 * button in tab order and inside the player in full screen, and it takes the
 * roles of the surface it is on (the media chip over a video).
 */
export function MediaVolume({
	media,
	className,
	glyphClassName,
	onOpenChange,
}: {
	media: MediaApi;
	className?: string;
	/** On the mute button: a row on the page surface lifts it off the ghost rest. */
	glyphClassName?: string;
	/** The panel opened or closed: a player keeps its bar up meanwhile. */
	onOpenChange?: (open: boolean) => void;
}) {
	const touch = useTouch();
	const level = media.muted ? 0 : media.volume;
	const percent = Math.round(level * 100);
	const Glyph = level === 0 ? VolumeX : level < 0.5 ? Volume1 : Volume2;
	const label = level === 0 ? "Unmute" : "Mute";

	const [box, setBox] = React.useState<HTMLDivElement | null>(null);
	const button = React.useRef<HTMLButtonElement>(null);
	const [open, setOpen] = React.useState(false);
	// `quiet`: put away with Escape, it stays shut until the pointer and focus
	// have both left, so handing focus back to the button does not reopen it.
	const live = React.useRef({
		open: false,
		hovered: false,
		focused: false,
		pressed: false,
		quiet: false,
	});
	const closing = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
	const report = React.useRef(onOpenChange);
	report.current = onOpenChange;

	const show = React.useCallback((next: boolean) => {
		clearTimeout(closing.current);
		if (live.current.open === next) return;
		live.current.open = next;
		setOpen(next);
		report.current?.(next);
	}, []);
	// Close soon, unless the pointer or keyboard focus is back by then.
	const settle = () => {
		clearTimeout(closing.current);
		closing.current = setTimeout(() => {
			if (!live.current.hovered && !live.current.focused) show(false);
		}, VOLUME_CLOSE_MS);
	};
	// An open panel tells the player it closed when the control goes away.
	React.useEffect(
		() => () => {
			clearTimeout(closing.current);
			if (live.current.open) report.current?.(false);
		},
		[],
	);

	if (touch) {
		return (
			<div
				data-slot="media-volume"
				data-state="closed"
				className={cn("flex items-center", className)}
			>
				<IconButton
					variant="ghost"
					size="sm"
					aria-label={label}
					className={glyphClassName}
					onClick={media.toggleMute}
				>
					<Glyph />
				</IconButton>
			</div>
		);
	}

	return (
		<Popover open={open} onOpenChange={(next) => !next && show(false)}>
			{/* biome-ignore lint/a11y/noStaticElementInteractions: hover and focus watched around a button and its panel, not a control of its own */}
			<div
				ref={setBox}
				data-slot="media-volume"
				data-state={open ? "open" : "closed"}
				className={cn("flex items-center", className)}
				onPointerEnter={() => {
					live.current.hovered = true;
					if (!live.current.quiet) show(true);
				}}
				onPointerLeave={(e) => {
					live.current.hovered = false;
					if (!live.current.focused) live.current.quiet = false;
					// A tap leaves as soon as the finger lifts: the panel stays for the
					// next touch, and a tap elsewhere puts it away.
					if (e.pointerType !== "touch") settle();
				}}
				// A focus that comes from a press is the pointer's, already handled by
				// hover: it must not hold the panel up after the pointer leaves.
				onPointerDown={() => {
					live.current.pressed = true;
				}}
				onPointerUp={() => {
					live.current.pressed = false;
				}}
				onPointerCancel={() => {
					live.current.pressed = false;
				}}
				onFocus={() => {
					if (live.current.pressed) return;
					live.current.focused = true;
					if (!live.current.quiet) show(true);
				}}
				onBlur={(e) => {
					if (box?.contains(e.relatedTarget as Node | null)) return;
					live.current.focused = false;
					if (!live.current.hovered) live.current.quiet = false;
					settle();
				}}
			>
				<PopoverAnchor asChild>
					<IconButton
						ref={button}
						variant="ghost"
						size="sm"
						aria-label={label}
						tip={tip(label, "M")}
						// The panel takes the top; the hint goes beside it.
						tipSide="right"
						className={glyphClassName}
						onClick={media.toggleMute}
					>
						<Glyph />
					</IconButton>
				</PopoverAnchor>
				<PopoverContent
					container={box}
					side="top"
					aria-label="Volume"
					data-slot="media-volume-panel"
					className="flex w-auto flex-col items-center gap-2 p-3"
					onOpenAutoFocus={(e) => e.preventDefault()}
					onCloseAutoFocus={(e) => e.preventDefault()}
					// The button is outside the panel but part of the control: pressing it
					// mutes and leaves the panel up.
					onInteractOutside={(e) => {
						if (box?.contains(e.target as Node | null)) e.preventDefault();
					}}
					// Escape from the slider hands focus back to the button, not the page.
					onEscapeKeyDown={() => {
						live.current.quiet = true;
						if (box?.contains(document.activeElement)) button.current?.focus();
					}}
				>
					<span
						aria-hidden="true"
						data-slot="media-volume-level"
						className="w-[4ch] text-center font-mono text-xs leading-none tabular-nums text-text-secondary"
					>
						{percent}%
					</span>
					<Slider
						size="sm"
						orientation="vertical"
						className="h-20"
						min={0}
						max={100}
						step={5}
						value={[percent]}
						onValueChange={([v]) => media.setVolume(v / 100)}
						thumbLabels={["Volume"]}
						thumbProps={{ "aria-valuetext": `${percent}%` }}
					/>
				</PopoverContent>
			</div>
		</Popover>
	);
}

/** Playback speed, a menu of the usual rates. */
export function MediaRate({
	media,
	onOpenChange,
}: {
	media: MediaApi;
	onOpenChange?: (open: boolean) => void;
}) {
	return (
		<DropdownMenu modal={false} onOpenChange={onOpenChange}>
			<DropdownMenuTrigger asChild>
				<Button
					variant="ghost"
					size="xs"
					aria-label={`Playback speed, ${formatRate(media.rate)}`}
					className="min-w-9 font-mono tabular-nums text-text-secondary"
					data-slot="media-rate"
				>
					{formatRate(media.rate)}
				</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end" side="top" className="min-w-28">
				<DropdownMenuLabel>Speed</DropdownMenuLabel>
				<DropdownMenuRadioGroup
					value={String(media.rate)}
					onValueChange={(v) => media.setRate(Number(v))}
				>
					{RATES.map((r) => (
						<DropdownMenuRadioItem key={r} value={String(r)} className="font-mono tabular-nums">
							{formatRate(r)}
						</DropdownMenuRadioItem>
					))}
				</DropdownMenuRadioGroup>
			</DropdownMenuContent>
		</DropdownMenu>
	);
}

export function MediaFullscreenButton({
	active,
	onToggle,
}: {
	active: boolean;
	onToggle: () => void;
}) {
	const label = active ? "Exit full screen" : "Full screen";
	return (
		<IconButton
			variant="ghost"
			size="sm"
			aria-label={label}
			tip={tip(label, "F")}
			tipSide="top"
			onClick={onToggle}
		>
			{active ? <Minimize /> : <Maximize />}
		</IconButton>
	);
}

/**
 * A link that saves the media. `href` is what the server hands out for a
 * download (a blob's `?download=1` url), so the file name is the server's.
 */
export function MediaDownloadButton({
	href,
	variant = "ghost",
	size = "sm",
	tipSide = "top",
	...props
}: { href: string } & Omit<IconButtonProps, "aria-label" | "asChild" | "children">) {
	return (
		<IconButton
			asChild
			variant={variant}
			size={size}
			aria-label="Download"
			tip="Download"
			tipSide={tipSide}
			data-slot="media-download"
			{...props}
		>
			<a href={href} download>
				<Download />
			</a>
		</IconButton>
	);
}

// ---------------------------------------------------------------------------
// The bar

export interface MediaControlsProps extends React.ComponentProps<"div"> {
	media: MediaApi;
	/** Draws the full screen toggle when given. */
	fullscreen?: { active: boolean; onToggle: () => void };
	/** Draws a download link to this url when given. */
	download?: string;
	/** The speed menu or the volume panel opened or closed: a player keeps its bar up meanwhile. */
	onMenuOpenChange?: (open: boolean) => void;
}

/** Scrub bar over a row of play, volume, time, speed, download and full screen. */
export function MediaControls({
	media,
	fullscreen,
	download,
	onMenuOpenChange,
	className,
	...props
}: MediaControlsProps) {
	// Up while either floating piece is: one closing must not drop the bar
	// while the other is still open.
	const up = React.useRef({ rate: false, volume: false });
	const report = (which: "rate" | "volume") => (open: boolean) => {
		const was = up.current.rate || up.current.volume;
		up.current[which] = open;
		const now = up.current.rate || up.current.volume;
		if (now !== was) onMenuOpenChange?.(now);
	};
	// Its own tooltip provider, like Timeline: the bar works dropped anywhere.
	return (
		<TooltipProvider>
			{/* biome-ignore lint/a11y/useSemanticElements: a cluster of controls, not a form section with a legend */}
			<div
				role="group"
				aria-label="Playback"
				data-slot="media-controls"
				className={cn("flex flex-col gap-0.5", className)}
				{...props}
			>
				<Scrubber
					time={media.time}
					duration={media.duration}
					buffered={media.buffered}
					onSeek={media.seek}
				/>
				<div className="flex items-center gap-0.5">
					<MediaPlayButton media={media} />
					<MediaVolume media={media} onOpenChange={report("volume")} />
					<MediaTime time={media.time} duration={media.duration} className="ml-1.5" />
					<div className="flex-1" />
					<MediaRate media={media} onOpenChange={report("rate")} />
					{download ? <MediaDownloadButton href={download} /> : null}
					{fullscreen ? <MediaFullscreenButton {...fullscreen} /> : null}
				</div>
			</div>
		</TooltipProvider>
	);
}
