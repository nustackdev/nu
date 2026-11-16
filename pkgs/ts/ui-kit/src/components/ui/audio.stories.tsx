import type { Meta, StoryObj } from "@storybook/react-vite";
import { Audio } from "./audio";

// CC0 and sample clips served with open CORS, so the waveform can decode them.
const ROAR = "https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3";
const sample = (s: number) => `https://samplelib.com/mp3/sample-${s}s.mp3`;
// Plays in an <audio>, but sends no CORS header: no waveform, the plain bar instead.
const NO_CORS = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3";

function Label({ children }: { children: React.ReactNode }) {
	return (
		<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="max-w-2xl p-8">
			<Audio src={sample(9)} />
		</div>
	),
};

export const WithTitle: StoryObj = {
	render: () => (
		<div className="max-w-2xl p-8">
			<Audio src={ROAR} title="t-rex-roar.mp3" />
		</div>
	),
};

export const WaveformFallback: StoryObj = {
	render: () => (
		<div className="max-w-2xl space-y-6 p-8">
			<div>
				<Label>source denies cors: plain bar</Label>
				<Audio src={NO_CORS} title="SoundHelix Song 1" />
			</div>
			<div>
				<Label>waveform off</Label>
				<Audio src={sample(6)} title="sample-6s.mp3" waveform={false} />
			</div>
			<div>
				<Label>peaks given, no decode</Label>
				<Audio
					src={sample(12)}
					title="sample-12s.mp3"
					peaks={Array.from(
						{ length: 160 },
						(_, i) => 0.25 + 0.7 * Math.abs(Math.sin(i / 9) * Math.cos(i / 23)),
					)}
				/>
			</div>
		</div>
	),
};

const TRACKS = [
	{ src: sample(3), title: "take-01 room tone.mp3" },
	{ src: sample(6), title: "take-02 voice.mp3" },
	{ src: sample(9), title: "take-03 voice, second pass with a long name that truncates.mp3" },
	{ src: ROAR, title: "t-rex-roar.mp3" },
	{ src: sample(12), title: "take-04 mixdown.mp3" },
	{ src: sample(15), title: "take-05 final.mp3" },
];

export const Stack: StoryObj = {
	render: () => (
		<div className="max-w-3xl p-8">
			<Label>a dense list: rows with lines between</Label>
			<div className="divide-y divide-border-subtle border-y border-border-subtle">
				{TRACKS.map((t) => (
					<Audio key={t.title} src={t.src} title={t.title} className="h-11" />
				))}
			</div>
		</div>
	),
};

export const States: StoryObj = {
	render: () => (
		<div className="max-w-2xl space-y-6 p-8">
			<div>
				<Label>source fails</Label>
				<Audio
					src="https://interactive-examples.mdn.mozilla.net/media/cc0-audio/missing.mp3"
					title="missing.mp3"
				/>
			</div>
			<div>
				<Label>no source</Label>
				<Audio title="untitled.mp3" />
			</div>
			<div>
				<Label>narrow</Label>
				<div className="w-80">
					<Audio src={ROAR} />
				</div>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Audio",
};

export default meta;
