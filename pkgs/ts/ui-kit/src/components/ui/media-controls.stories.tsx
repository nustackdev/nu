import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect, useState } from "react";
import { clampTime, knownDuration, timeAt } from "../../lib/media/model";
import {
	EMPTY_SNAPSHOT,
	type MediaApi,
	type MediaSnapshot,
	useMedia,
} from "../../lib/media/use-media";
import { MediaControls, MediaTime, Scrubber } from "./media-controls";
import { Spinner } from "./spinner";

const AUDIO_SRC = "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3";

/**
 * A transport with no element behind it: state you set, actions that move
 * it. `ticking` runs the clock while playing, so the bar moves like the real
 * thing.
 */
function useFake(initial: Partial<MediaSnapshot>, ticking = false): MediaApi {
	const [s, setS] = useState<MediaSnapshot>({ ...EMPTY_SNAPSHOT, ready: true, ...initial });
	const set = (patch: Partial<MediaSnapshot>) => setS((p) => ({ ...p, ...patch }));
	useEffect(() => {
		if (!ticking || !s.playing || s.waiting) return;
		const id = setInterval(
			() => setS((p) => ({ ...p, time: (p.time + 0.25 * p.rate) % p.duration })),
			250,
		);
		return () => clearInterval(id);
	}, [ticking, s.playing, s.waiting]);
	const seek = (t: number) => set({ time: clampTime(t, s.duration), ended: false });
	return {
		...s,
		ref: () => {},
		el: null,
		play: () => set({ playing: true, ended: false }),
		pause: () => set({ playing: false }),
		toggle: () => set({ playing: !s.playing, ended: false }),
		seek,
		seekBy: (dt) => seek(s.time + dt),
		seekFraction: (f) => knownDuration(s.duration) && seek(timeAt(f, s.duration)),
		setVolume: (v) => set({ volume: v, muted: v <= 0 }),
		setMuted: (muted) => set({ muted }),
		toggleMute: () => set({ muted: !s.muted }),
		setRate: (rate) => set({ rate }),
	};
}

function Frame({ label, children }: { label: string; children: React.ReactNode }) {
	return (
		<div>
			<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
				{label}
			</div>
			<div className="rounded-md border border-border-subtle px-3 pb-1.5 pt-3">{children}</div>
		</div>
	);
}

export const Playing: StoryObj = {
	render: function Story() {
		const media = useFake({ playing: true, time: 42, duration: 225, buffered: 140 }, true);
		return (
			<div className="max-w-xl p-8">
				<Frame label="playing">
					<MediaControls media={media} />
				</Frame>
			</div>
		);
	},
};

export const States: StoryObj = {
	render: function Story() {
		const paused = useFake({ time: 12, duration: 225, buffered: 60 });
		const buffering = useFake({
			playing: true,
			waiting: true,
			time: 96,
			duration: 225,
			buffered: 97,
		});
		const muted = useFake({ muted: true, time: 30, duration: 225, buffered: 225, rate: 1.5 });
		const ended = useFake({ ended: true, time: 225, duration: 225, buffered: 225 });
		const long = useFake({ time: 754, duration: 5520, buffered: 1200, volume: 0.3 });
		const unknown = useFake({ ready: false, duration: Number.NaN });
		return (
			<div className="max-w-xl space-y-6 p-8">
				<Frame label="paused">
					<MediaControls media={paused} />
				</Frame>
				<Frame label="buffering">
					<div className="relative">
						<MediaControls media={buffering} />
						<Spinner size="sm" tone="neutral" className="absolute right-0 top-0" />
					</div>
				</Frame>
				<Frame label="muted, 1.5x">
					<MediaControls media={muted} />
				</Frame>
				<Frame label="ended">
					<MediaControls media={ended} />
				</Frame>
				<Frame label="over an hour, quiet">
					<MediaControls media={long} />
				</Frame>
				<Frame label="duration unknown">
					<MediaControls media={unknown} />
				</Frame>
			</div>
		);
	},
};

export const ScrubberAlone: StoryObj = {
	render: function Story() {
		const [time, setTime] = useState(48);
		return (
			<div className="max-w-md space-y-3 p-8">
				<Scrubber time={time} duration={180} buffered={120} onSeek={setTime} label="Seek" />
				<MediaTime time={time} duration={180} />
			</div>
		);
	},
};

export const BoundToElement: StoryObj = {
	render: function Story() {
		const media = useMedia();
		return (
			<div className="max-w-xl p-8">
				{/* biome-ignore lint/a11y/useMediaCaption: a sound effect, nothing spoken */}
				<audio ref={media.ref} src={AUDIO_SRC} preload="metadata" />
				<Frame label="a real <audio>, no player around it">
					<MediaControls media={media} />
				</Frame>
			</div>
		);
	},
};

/**
 * Filling its column. In touch mode the scrub thumb always shows, every
 * piece has a 44px tap area, and volume is the mute button alone.
 */
export const Touch: StoryObj = {
	render: function Story() {
		const media = useFake({ playing: true, time: 42, duration: 225, buffered: 140 });
		return (
			<div className="p-4">
				<Frame label="playing">
					<MediaControls
						media={media}
						download={AUDIO_SRC}
						fullscreen={{ active: false, onToggle: () => {} }}
					/>
				</Frame>
			</div>
		);
	},
};

const meta: Meta = {
	title: "UI/Media Controls",
};

export default meta;
