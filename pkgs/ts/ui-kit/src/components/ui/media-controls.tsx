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
				<ScrubBar played={played} buffered={fractionOf(buffered, duration)} />
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

/** The plain scrub track: loaded run, played run, and a thumb on hover, focus or drag. */
function ScrubBar({ played, buffered }: { played: number; buffered: number }) {
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
 * Mute, and a volume slider that opens beside it on hover or focus: the level
 * is there when you reach for it and out of the way otherwise.
 */
export function MediaVolume({
	media,
	className,
	glyphClassName,
}: {
	media: MediaApi;
	className?: string;
	/** On the mute button: a row on the page surface lifts it off the ghost rest. */
	glyphClassName?: string;
}) {
	const level = media.muted ? 0 : media.volume;
	const Glyph = level === 0 ? VolumeX : level < 0.5 ? Volume1 : Volume2;
	const label = level === 0 ? "Unmute" : "Mute";
	return (
		<div data-slot="media-volume" className={cn("group/volume flex items-center", className)}>
			<IconButton
				variant="ghost"
				size="sm"
				aria-label={label}
				tip={tip(label, "M")}
				tipSide="top"
				className={glyphClassName}
				onClick={media.toggleMute}
			>
				<Glyph />
			</IconButton>
			<div
				className={cn(
					"w-0 overflow-hidden opacity-0",
					"transition-[width,opacity] duration-fast ease-out",
					"group-hover/volume:w-20 group-hover/volume:opacity-100",
					"group-focus-within/volume:w-20 group-focus-within/volume:opacity-100",
				)}
			>
				<Slider
					size="sm"
					className="w-20 px-2"
					min={0}
					max={100}
					step={5}
					value={[Math.round(level * 100)]}
					onValueChange={([v]) => media.setVolume(v / 100)}
					thumbLabels={["Volume"]}
					thumbProps={{ "aria-valuetext": `${Math.round(level * 100)}%` }}
				/>
			</div>
		</div>
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
	/** The speed menu opened or closed: a player keeps its bar up meanwhile. */
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
					<MediaVolume media={media} />
					<MediaTime time={media.time} duration={media.duration} className="ml-1.5" />
					<div className="flex-1" />
					<MediaRate media={media} onOpenChange={onMenuOpenChange} />
					{download ? <MediaDownloadButton href={download} /> : null}
					{fullscreen ? <MediaFullscreenButton {...fullscreen} /> : null}
				</div>
			</div>
		</TooltipProvider>
	);
}
