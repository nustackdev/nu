// Audio primitive: one dense row that plays a sound. Play, an optional title,
// a waveform you scrub, the time, volume and speed.
//
// The waveform is the source's own (lib/media/peaks.ts): fetched, decoded
// with Web Audio and drawn as thin bars, the played part in accent, the part
// under a hovering pointer a step brighter, the rest quiet. Until the decode
// lands the bars lie flat, so nothing jumps; when it cannot happen (the
// source denies CORS, Web Audio lacks the codec) the row falls back to the
// plain scrub bar. `peaks` skips the decode for a caller that has them
// already; `waveform={false}` skips it altogether.
//
// `download` ends the row with a download link.
//
// The row fits its container: under 24rem it drops the speed menu, under
// 20rem the volume too, and a long title gives way before the waveform, so
// play, the waveform, the time and the download always show. A phone is
// about 22rem wide.
//
// The row takes focus and owns the transport keys like Video, with `,` and
// `.` stepping a tenth of a second while paused. It draws no box of its own:
// rows stack into a list with lines between them, like any dense list.

import { TriangleAlert } from "lucide-react";
import * as React from "react";
import { resamplePeaks } from "../../lib/media/model";
import { loadPeaks } from "../../lib/media/peaks";
import { useMedia, useMediaKeys } from "../../lib/media/use-media";
import { cn } from "../../lib/utils";
import {
	MediaDownloadButton,
	MediaPlayButton,
	MediaRate,
	MediaTime,
	MediaVolume,
	Scrubber,
	type ScrubTrackState,
} from "./media-controls";
import { TooltipProvider } from "./tooltip";

/** Seconds `,` and `.` step: audio has no frames, a tenth reads as fine. */
const FINE_STEP = 0.1;

export interface AudioProps
	extends Omit<
		React.AudioHTMLAttributes<HTMLAudioElement>,
		"controls" | "className" | "style" | "title"
	> {
	/** A name shown before the waveform, and the player's accessible name. */
	title?: string;
	/** The accessible name when there is no title. */
	label?: string;
	/** False draws the plain scrub bar and never fetches the source for a waveform. */
	waveform?: boolean;
	/** Peaks in [0, 1], already computed: drawn as given, no decode. */
	peaks?: ArrayLike<number>;
	/** A url that saves the sound: a download link at the end of the row. */
	download?: string;
	/** Classes and styles for the row, not the <audio> inside it. */
	className?: string;
	style?: React.CSSProperties;
}

/** The source's peaks: undefined while they load, null when there will be none. */
function usePeaks(src: string | undefined, on: boolean, given?: ArrayLike<number>) {
	const [peaks, setPeaks] = React.useState<ArrayLike<number> | null | undefined>(given);
	React.useEffect(() => {
		if (given) {
			setPeaks(given);
			return;
		}
		if (!on || !src) {
			setPeaks(null);
			return;
		}
		let live = true;
		setPeaks(undefined);
		loadPeaks(src).then((got) => live && setPeaks(got));
		return () => {
			live = false;
		};
	}, [src, on, given]);
	return peaks;
}

function useWidth(ref: React.RefObject<HTMLElement | null>) {
	const [width, setWidth] = React.useState(0);
	React.useEffect(() => {
		const node = ref.current;
		if (!node || typeof ResizeObserver === "undefined") return;
		const watch = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)));
		watch.observe(node);
		return () => watch.disconnect();
	}, [ref]);
	return width;
}

const BAR = 2;
const PITCH = 4;
const HEIGHT = 28;
const MIN_BAR = 2;

/** One layer of bars in the current color, clipped to show the first `upTo` of it. */
function Bars({
	bars,
	width,
	upTo,
	className,
}: {
	bars: React.ReactNode;
	width: number;
	upTo: number;
	className: string;
}) {
	return (
		<svg
			aria-hidden="true"
			className={cn("absolute inset-0 size-full", className)}
			viewBox={`0 0 ${Math.max(1, width)} ${HEIGHT}`}
			preserveAspectRatio="none"
			style={upTo < 1 ? { clipPath: `inset(0 ${(1 - upTo) * 100}% 0 0)` } : undefined}
		>
			{bars}
		</svg>
	);
}

function WaveTrack({ peaks, played, hover }: { peaks: ArrayLike<number> } & ScrubTrackState) {
	const box = React.useRef<HTMLSpanElement>(null);
	const width = useWidth(box);
	const count = Math.max(1, Math.floor((width + PITCH - BAR) / PITCH));
	const bars = React.useMemo(
		() =>
			resamplePeaks(peaks, count).map((p, i) => {
				const h = Math.max(MIN_BAR, p * HEIGHT);
				return (
					<rect
						// biome-ignore lint/suspicious/noArrayIndexKey: a bar is its position.
						key={i}
						x={i * PITCH}
						y={(HEIGHT - h) / 2}
						width={BAR}
						height={h}
						rx={BAR / 2}
						fill="currentColor"
					/>
				);
			}),
		[peaks, count],
	);
	return (
		<span ref={box} data-slot="waveform" className="relative h-full w-full">
			<Bars bars={bars} width={width} upTo={1} className="text-border-strong" />
			{hover !== null && hover > played ? (
				<Bars bars={bars} width={width} upTo={hover} className="text-text-muted" />
			) : null}
			<Bars bars={bars} width={width} upTo={played} className="text-accent" />
		</span>
	);
}

const FLAT: ArrayLike<number> = [];

export function Audio({
	src,
	title,
	label,
	waveform = true,
	peaks: given,
	download,
	className,
	style,
	children,
	...props
}: AudioProps) {
	const media = useMedia();
	const keys = useMediaKeys(media, { fineStep: FINE_STEP });
	const peaks = usePeaks(src, waveform, given);
	const failed = !!src && media.error;

	const track =
		peaks === null ? undefined : (s: ScrubTrackState) => <WaveTrack peaks={peaks ?? FLAT} {...s} />;

	return (
		<TooltipProvider>
			{/* biome-ignore lint/a11y/useSemanticElements: a focusable surface that owns its keys, not a form section */}
			<div
				data-slot="audio"
				data-state={media.playing ? "playing" : "paused"}
				role="group"
				aria-roledescription="audio player"
				aria-label={title || label || "Audio"}
				aria-keyshortcuts="Space K J L ArrowLeft ArrowRight M"
				{...keys}
				className={cn(
					"@container/audio flex h-10 w-full min-w-0 items-center gap-2 rounded-md px-1",
					"cursor-default select-none outline-hidden",
					"focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
					className,
				)}
				style={style}
			>
				{src ? (
					<audio ref={media.ref} src={src} preload="metadata" {...props}>
						{children}
					</audio>
				) : null}
				<MediaPlayButton
					media={media}
					variant="default"
					size="md"
					className="rounded-full"
					disabled={!src || failed}
				/>
				{title ? (
					<span
						data-slot="audio-title"
						title={title}
						className="w-[28%] max-w-56 min-w-0 truncate text-sm text-text-primary"
					>
						{title}
					</span>
				) : null}
				{src && !failed ? (
					<Scrubber
						className="h-8 min-w-16 flex-1"
						time={media.time}
						duration={media.duration}
						buffered={media.buffered}
						onSeek={media.seek}
					>
						{track}
					</Scrubber>
				) : (
					<span className="flex min-w-16 flex-1 items-center gap-1.5 text-xs text-text-muted">
						{failed ? (
							<TriangleAlert aria-hidden="true" className="size-3.5 text-status-danger" />
						) : null}
						{failed ? "Audio could not load" : "No audio"}
					</span>
				)}
				<MediaTime time={media.time} duration={media.duration} />
				{/* A narrow row keeps play, the waveform and the time: speed goes first, then volume. */}
				<span className="flex shrink-0 @max-xs/audio:hidden">
					<MediaVolume media={media} glyphClassName="text-text-primary" />
				</span>
				<span className="flex shrink-0 @max-sm/audio:hidden">
					<MediaRate media={media} />
				</span>
				{download ? <MediaDownloadButton href={download} className="text-text-primary" /> : null}
			</div>
		</TooltipProvider>
	);
}
