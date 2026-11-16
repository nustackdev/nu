// Video primitive: a native <video> with the kit transport over its frame.
//
// The frame holds its shape like Image does: `aspectRatio` when given, else
// the video's own once its metadata is in (16 / 9 until then), so the page
// does not jump when it loads. `fit`, `radius` and `poster` behave as on an
// image.
//
// The transport (media-controls.tsx) sits at the bottom on a scrim. It shows
// while paused, while the pointer moves, while a control has keyboard focus
// or the speed menu is open, and fades out once playback runs idle; the
// cursor goes with it. The frame is a dark stage in both themes, the way a
// screen is: the scrim, the controls and the focus ring all resolve against
// dark tokens, so they read over any picture.
//
// The frame takes focus and owns the transport keys (lib/media/model.ts
// `keyCommand`): space or k, j l and the arrows, `,` and `.` to step one
// frame while paused (`fps`, 30 unless told), m, f, and 0 to 9. A click
// plays or pauses, a double click goes full screen.
//
// Captions go in as children: `<track kind="captions" ... />`.

import { VideoOff } from "lucide-react";
import * as React from "react";
import { useMedia, useMediaKeys } from "../../lib/media/use-media";
import { cn } from "../../lib/utils";
import { EmptyState } from "./empty-state";
import { MediaControls } from "./media-controls";
import { Spinner } from "./spinner";

const RADIUS_CLASS = {
	none: "rounded-none",
	sm: "rounded-sm",
	md: "rounded-md",
	lg: "rounded-lg",
} as const;

const FIT_CLASS = {
	contain: "object-contain",
	cover: "object-cover",
	fill: "object-fill",
} as const;

/** How long the transport stays up after the pointer last moved, while playing. */
const IDLE_MS = 2200;

export interface VideoProps
	extends Omit<React.VideoHTMLAttributes<HTMLVideoElement>, "controls" | "className" | "style"> {
	radius?: keyof typeof RADIUS_CLASS;
	fit?: keyof typeof FIT_CLASS;
	/** A CSS aspect ratio ("16 / 9") the frame keeps; the video's own when left out. */
	aspectRatio?: string;
	/** Frames per second, for the one frame step on `,` and `.`. */
	fps?: number;
	/** The player's accessible name. */
	label?: string;
	/** False drops the transport: the frame still plays on click and keys. */
	controls?: boolean;
	/** Classes and styles for the frame, not the <video> inside it. */
	className?: string;
	style?: React.CSSProperties;
}

function useFullscreen(target: React.RefObject<HTMLElement | null>) {
	const [active, setActive] = React.useState(false);
	const supported = typeof document !== "undefined" && document.fullscreenEnabled === true;
	React.useEffect(() => {
		const sync = () =>
			setActive(document.fullscreenElement === target.current && target.current !== null);
		document.addEventListener("fullscreenchange", sync);
		return () => document.removeEventListener("fullscreenchange", sync);
	}, [target]);
	const toggle = React.useCallback(() => {
		const el = target.current;
		if (!el) return;
		if (document.fullscreenElement === el) document.exitFullscreen().catch(() => {});
		else el.requestFullscreen().catch(() => {});
	}, [target]);
	return { supported, active, toggle };
}

export function Video({
	src,
	radius = "md",
	fit = "contain",
	aspectRatio,
	fps = 30,
	label = "Video",
	controls = true,
	className,
	style,
	children,
	...props
}: VideoProps) {
	const media = useMedia();
	const frame = React.useRef<HTMLDivElement>(null);
	const fullscreen = useFullscreen(frame);
	const [natural, setNatural] = React.useState<string | null>(null);
	const [active, setActive] = React.useState(false);
	const [menuOpen, setMenuOpen] = React.useState(false);
	const idle = React.useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

	React.useEffect(() => () => clearTimeout(idle.current), []);
	// A new source starts from its own shape, not the last one's.
	// biome-ignore lint/correctness/useExhaustiveDependencies: reset on src change only.
	React.useEffect(() => setNatural(null), [src]);

	const poke = () => {
		setActive(true);
		clearTimeout(idle.current);
		idle.current = setTimeout(() => setActive(false), IDLE_MS);
	};

	const keys = useMediaKeys(media, {
		fineStep: 1 / (fps > 0 ? fps : 30),
		onFullscreen: fullscreen.supported ? fullscreen.toggle : undefined,
	});

	const shown = !media.playing || active || menuOpen;
	const empty = !src;
	const failed = !empty && media.error;

	return (
		// biome-ignore lint/a11y/useSemanticElements: a focusable surface that owns its keys, not a form section
		<div
			ref={frame}
			data-slot="video"
			data-state={media.playing ? "playing" : "paused"}
			role="group"
			aria-roledescription="video player"
			aria-label={label}
			aria-keyshortcuts="Space K J L ArrowLeft ArrowRight M F"
			className={cn(
				"dark group/video relative w-full overflow-hidden bg-bg-sunken text-text-primary",
				"cursor-default select-none outline-hidden",
				"focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
				"[&:fullscreen]:rounded-none",
				RADIUS_CLASS[radius],
				!shown && "cursor-none",
				className,
			)}
			style={{ aspectRatio: aspectRatio ?? natural ?? "16 / 9", ...style }}
			{...keys}
			onKeyDownCapture={poke}
			onPointerMove={poke}
			onPointerLeave={() => {
				clearTimeout(idle.current);
				setActive(false);
			}}
		>
			{empty ? null : (
				<video
					ref={media.ref}
					src={src}
					preload="metadata"
					playsInline
					{...props}
					className={cn(
						"absolute inset-0 size-full",
						FIT_CLASS[fullscreen.active ? "contain" : fit],
						failed && "invisible",
					)}
					onLoadedMetadata={(e) => {
						const v = e.currentTarget;
						if (v.videoWidth > 0 && v.videoHeight > 0)
							setNatural(`${v.videoWidth} / ${v.videoHeight}`);
						props.onLoadedMetadata?.(e);
					}}
					onClick={media.toggle}
					onDoubleClick={fullscreen.supported ? fullscreen.toggle : undefined}
				>
					{children}
				</video>
			)}

			{empty || failed ? (
				<EmptyState
					className="absolute inset-0"
					size="sm"
					icon={<VideoOff aria-hidden="true" />}
					description={failed ? "The source failed to load or play." : undefined}
				>
					{failed ? "Video could not load" : "No video"}
				</EmptyState>
			) : null}

			{media.waiting && !failed ? (
				<div className="pointer-events-none absolute inset-0 flex items-center justify-center">
					<Spinner size="xl" tone="neutral" label="Buffering" />
				</div>
			) : null}

			{controls && !empty && !failed ? (
				<div
					data-slot="video-controls"
					data-shown={shown ? "" : undefined}
					className={cn(
						"absolute inset-x-0 bottom-0 bg-linear-to-t from-bg-overlay to-transparent px-2.5 pt-8 pb-1",
						"opacity-0 transition-opacity duration-base ease-out",
						"data-shown:opacity-100 has-focus-visible:opacity-100",
					)}
				>
					<MediaControls
						media={media}
						fullscreen={
							fullscreen.supported
								? { active: fullscreen.active, onToggle: fullscreen.toggle }
								: undefined
						}
						onMenuOpenChange={setMenuOpen}
					/>
				</div>
			) : null}
		</div>
	);
}
