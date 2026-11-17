import type { Meta, StoryObj } from "@storybook/react-vite";
import * as React from "react";
import { type FakeFail, type FakeMedia, installFakeMedia } from "../../lib/capture/fake-media";
import { sinkParameters, ThemePair } from "../../stories/kitchen-sink/frame";
import { MicCapture, type MicCaptureProps, type MicTake } from "./mic-capture";

// The control drawn light and dark, over fake microphones (an oscillator that
// talks, recorded by the browser's real MediaRecorder). A state that needs a
// device is reached the way a person reaches it: the story clicks Record
// (and Pause, or unplugs) after mount. A take that needs none is a short wav
// made here.

let media: FakeMedia | null = null;

/** A story's `beforeEach`: fake mics for the story, the real ones back after. */
function fakes(opts: { mics?: number; fail?: FakeFail; insecure?: boolean } = {}) {
	return () => {
		media = installFakeMedia({ mics: opts.mics ?? 1, fail: opts.fail, delayMs: 300 });
		if (opts.insecure) {
			Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
		}
		return () => {
			media?.restore();
			media = null;
		};
	};
}

/** A few seconds of a tone that rises and falls like a voice, as a wav. */
function wav(seconds: number): Blob {
	const rate = 22050;
	const n = Math.floor(rate * seconds);
	const data = new DataView(new ArrayBuffer(44 + n * 2));
	const text = (at: number, s: string) => {
		for (let i = 0; i < s.length; i++) data.setUint8(at + i, s.charCodeAt(i));
	};
	text(0, "RIFF");
	data.setUint32(4, 36 + n * 2, true);
	text(8, "WAVE");
	text(12, "fmt ");
	data.setUint32(16, 16, true);
	data.setUint16(20, 1, true);
	data.setUint16(22, 1, true);
	data.setUint32(24, rate, true);
	data.setUint32(28, rate * 2, true);
	data.setUint16(32, 2, true);
	data.setUint16(34, 16, true);
	text(36, "data");
	data.setUint32(40, n * 2, true);
	for (let i = 0; i < n; i++) {
		const t = i / rate;
		const words = Math.max(0, Math.sin(t * Math.PI * 1.6)) ** 2;
		const v =
			Math.sin(2 * Math.PI * 160 * t) * 0.5 * words +
			Math.sin(2 * Math.PI * 320 * t) * 0.15 * words;
		data.setInt16(44 + i * 2, Math.round(v * 0x7fff), true);
	}
	return new Blob([data.buffer], { type: "audio/wav" });
}

const TAKE: MicTake = { blob: wav(4), duration: 4 };

/** The control with its take held, so every button works in the story. */
function Mic({
	initial = null,
	...props
}: Partial<MicCaptureProps> & { initial?: MicTake | null }) {
	const [take, setTake] = React.useState<MicTake | null>(initial);
	return (
		<MicCapture
			take={take}
			onTake={(file, meta) => setTake({ blob: file, duration: meta.duration })}
			onDiscard={() => setTake(null)}
			{...props}
		/>
	);
}

type Step = { click: string } | { wait: number } | { lose: true };

/** Plays steps on the control inside, once after mount: a person's clicks. */
function Driven({ steps, children }: { steps: Step[]; children: React.ReactNode }) {
	const box = React.useRef<HTMLDivElement>(null);
	// biome-ignore lint/correctness/useExhaustiveDependencies: plays once.
	React.useEffect(() => {
		let on = true;
		const run = async () => {
			for (const s of steps) {
				if (!on) return;
				if ("wait" in s) await new Promise((r) => setTimeout(r, s.wait));
				else if ("lose" in s) media?.lose();
				else {
					const found = [...(box.current?.querySelectorAll("button") ?? [])].find(
						(b) => b.getAttribute("aria-label") === s.click || b.textContent?.trim() === s.click,
					);
					found?.click();
					await new Promise((r) => setTimeout(r, 450));
				}
			}
		};
		void run();
		return () => {
			on = false;
		};
	}, []);
	return <div ref={box}>{children}</div>;
}

function Caption({ children }: { children: React.ReactNode }) {
	return (
		<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

function Block({ caption, children }: { caption: string; children: React.ReactNode }) {
	return (
		<div className="max-w-xl">
			<Caption>{caption}</Caption>
			{children}
		</div>
	);
}

export const Idle: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="idle: click Record (fake mic)">
				<Mic />
			</Block>
			<Block caption="with a max duration">
				<Mic maxDuration={60} />
			</Block>
		</ThemePair>
	),
};

export const Sizes: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			{(["sm", "md", "lg"] as const).map((s) => (
				<Block key={s} caption={s}>
					<div className="flex flex-col gap-2">
						<Mic size={s} maxDuration={90} />
						<Mic size={s} initial={TAKE} />
					</div>
				</Block>
			))}
		</ThemePair>
	),
};

export const Recording: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="recording, with a max">
				<Driven steps={[{ click: "Record" }]}>
					<Mic maxDuration={60} />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const Paused: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="paused: the dot still, the time held">
				<Driven steps={[{ click: "Record" }, { wait: 1500 }, { click: "Pause recording" }]}>
					<Mic />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const Take: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="a take: play it, record again, delete">
				<Mic initial={TAKE} />
			</Block>
			<Block caption="invalid (a required field left empty)">
				<Mic invalid />
			</Block>
		</ThemePair>
	),
};

export const ReadOnly: StoryObj = {
	render: () => (
		<ThemePair>
			<Block caption="read only, a take: plays, nothing else">
				<Mic readOnly initial={TAKE} />
			</Block>
			<Block caption="read only, empty">
				<Mic readOnly />
			</Block>
		</ThemePair>
	),
};

export const Disabled: StoryObj = {
	render: () => (
		<ThemePair>
			<Block caption="disabled">
				<Mic disabled maxDuration={60} />
			</Block>
			<Block caption="disabled, a take">
				<Mic disabled initial={TAKE} />
			</Block>
		</ThemePair>
	),
};

export const TwoMics: StoryObj = {
	beforeEach: fakes({ mics: 2 }),
	render: () => (
		<ThemePair>
			<Block caption="two mics: the menu shows once they are known (after a first take)">
				<Driven steps={[{ click: "Record" }, { wait: 1500 }, { click: "Stop" }]}>
					<Mic />
				</Driven>
			</Block>
		</ThemePair>
	),
};

function blocked(caption: string, opts: Parameters<typeof fakes>[0]): StoryObj {
	return {
		beforeEach: fakes(opts),
		render: () => (
			<ThemePair>
				<Block caption={caption}>
					<Driven steps={[{ click: "Record" }]}>
						<Mic />
					</Driven>
				</Block>
			</ThemePair>
		),
	};
}

export const BlockedDenied = blocked("blocked: denied", { fail: "denied" });
export const BlockedNoDevice = blocked("blocked: no device", { fail: "no_device" });
export const BlockedBusy = blocked("blocked: busy", { fail: "busy" });
export const BlockedInsecure = blocked("blocked: insecure, no retry", { insecure: true });

export const Lost: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="lost mid take: what was recorded is kept">
				<Driven steps={[{ click: "Record" }, { wait: 2000 }, { lose: true }]}>
					<Mic />
				</Driven>
			</Block>
		</ThemePair>
	),
};

const meta: Meta = {
	title: "UI/MicCapture",
	parameters: sinkParameters,
};

export default meta;
