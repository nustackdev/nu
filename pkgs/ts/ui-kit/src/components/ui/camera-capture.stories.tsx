import type { Meta, StoryObj } from "@storybook/react-vite";
import * as React from "react";
import { type FakeFail, type FakeMedia, installFakeMedia } from "../../lib/capture/fake-media";
import { sinkParameters, ThemePair } from "../../stories/kitchen-sink/frame";
import { CameraCapture, type CameraCaptureProps, type CameraTake } from "./camera-capture";

// The control drawn light and dark, over fake cameras (a canvas animation per
// camera, recorded by the browser's real MediaRecorder). A state that needs a
// camera is reached the way a person reaches it: the story clicks Open camera
// (and records, or unplugs) after mount. A photo take is drawn here; a video
// take is recorded in the story, with no sound: a click from a script is no
// user gesture, so the fake microphone's AudioContext stays suspended, and a
// recorder waiting on a silent track writes no bytes.

let media: FakeMedia | null = null;

/** A story's `beforeEach`: fake cameras for the story, the real ones back after. */
function fakes(
	opts: { cameras?: number; fail?: FakeFail; insecure?: boolean; unsupported?: boolean } = {},
) {
	return () => {
		media = installFakeMedia({ cameras: opts.cameras ?? 1, fail: opts.fail, delayMs: 300 });
		const recorder = (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
		if (opts.insecure) {
			Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
		}
		if (opts.unsupported) (globalThis as { MediaRecorder?: unknown }).MediaRecorder = undefined;
		return () => {
			(globalThis as { MediaRecorder?: unknown }).MediaRecorder = recorder;
			media?.restore();
			media = null;
		};
	};
}

/** A photo drawn on a canvas, the way a camera frame would land. */
function usePhoto(width = 1280, height = 720): CameraTake | null {
	const [take, setTake] = React.useState<CameraTake | null>(null);
	React.useEffect(() => {
		const canvas = document.createElement("canvas");
		canvas.width = width;
		canvas.height = height;
		const g = canvas.getContext("2d");
		if (!g) return;
		const grad = g.createLinearGradient(0, 0, width, height);
		grad.addColorStop(0, "hsl(265 45% 22%)");
		grad.addColorStop(1, "hsl(305 55% 40%)");
		g.fillStyle = grad;
		g.fillRect(0, 0, width, height);
		g.beginPath();
		g.arc(width * 0.62, height * 0.45, Math.min(width, height) / 5, 0, Math.PI * 2);
		g.fillStyle = "hsl(85 70% 70% / 0.85)";
		g.fill();
		canvas.toBlob(
			(blob) => blob && setTake({ blob, mime: blob.type, duration: 0, width, height }),
			"image/jpeg",
			0.92,
		);
	}, [width, height]);
	return take;
}

/** The control with its take held, so every button works in the story. */
function Cam({
	initial = null,
	...props
}: Partial<CameraCaptureProps> & { initial?: CameraTake | null }) {
	const [take, setTake] = React.useState<CameraTake | null>(initial);
	React.useEffect(() => setTake(initial), [initial]);
	return (
		<CameraCapture
			take={take}
			onTake={(file, meta) => setTake({ blob: file, mime: file.type, ...meta })}
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

function Block({ caption, children }: { caption: string; children: React.ReactNode }) {
	return (
		<div className="max-w-md">
			<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
				{caption}
			</div>
			{children}
		</div>
	);
}

const OPEN: Step[] = [{ click: "Open camera" }];
const RECORD: Step[] = [...OPEN, { wait: 300 }, { click: "Start recording" }];

export const Idle: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="photo, idle: click Open camera (fake camera)">
				<Cam />
			</Block>
			<Block caption="video, idle, sm">
				<Cam mode="video" size="sm" />
			</Block>
		</ThemePair>
	),
};

export const LivePhoto: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="live, photo: the shutter; the preview mirrored">
				<Driven steps={OPEN}>
					<Cam />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const LiveVideo: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="live, video: record">
				<Driven steps={OPEN}>
					<Cam mode="video" maxDuration={60} />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const TwoCameras: StoryObj = {
	beforeEach: fakes({ cameras: 2 }),
	render: () => (
		<ThemePair>
			<Block caption="two cameras: flip and the camera menu">
				<Driven steps={OPEN}>
					<Cam />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const Recording: StoryObj = {
	beforeEach: fakes({ cameras: 2 }),
	render: () => (
		<ThemePair>
			<Block caption="recording, with a max: flip and menu hide">
				<Driven steps={RECORD}>
					<Cam mode="video" maxDuration={60} />
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
				<Driven steps={[...RECORD, { wait: 1500 }, { click: "Pause recording" }]}>
					<Cam mode="video" />
				</Driven>
			</Block>
		</ThemePair>
	),
};

function PhotoTake(props: Partial<CameraCaptureProps>) {
	const photo = usePhoto();
	return <Cam initial={photo} {...props} />;
}

export const PhotoTaken: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="a photo: click it to view, retake, delete">
				<PhotoTake />
			</Block>
			<Block caption="invalid (a required field left empty)">
				<Cam invalid />
			</Block>
		</ThemePair>
	),
};

export const VideoTaken: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="a video, recorded here for 2s: play, retake, delete">
				<Driven steps={[...RECORD, { wait: 2000 }, { click: "Stop and keep" }]}>
					<Cam mode="video" audio={false} />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const Square: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="aspect 1/1, idle">
				<Cam aspect="1/1" />
			</Block>
			<Block caption="aspect 1/1, live">
				<Driven steps={OPEN}>
					<Cam aspect="1/1" />
				</Driven>
			</Block>
		</ThemePair>
	),
};

function Blocked({ caption, video = false }: { caption: string; video?: boolean }) {
	return (
		<ThemePair>
			<Block caption={caption}>
				<Driven steps={OPEN}>
					<Cam mode={video ? "video" : "photo"} />
				</Driven>
			</Block>
		</ThemePair>
	);
}

export const BlockedDenied: StoryObj = {
	beforeEach: fakes({ fail: "denied" }),
	render: () => <Blocked caption="blocked: denied, try again" />,
};

export const BlockedNoDevice: StoryObj = {
	beforeEach: fakes({ fail: "no_device" }),
	render: () => <Blocked caption="blocked: no camera" />,
};

export const BlockedBusy: StoryObj = {
	beforeEach: fakes({ fail: "busy" }),
	render: () => <Blocked caption="blocked: in use elsewhere" />,
};

export const BlockedInsecure: StoryObj = {
	beforeEach: fakes({ insecure: true }),
	render: () => <Blocked caption="blocked: not https, no retry" />,
};

export const BlockedUnsupported: StoryObj = {
	beforeEach: fakes({ unsupported: true }),
	render: () => <Blocked caption="blocked: video with no MediaRecorder" video />,
};

export const Lost: StoryObj = {
	beforeEach: fakes(),
	render: () => (
		<ThemePair>
			<Block caption="lost while live">
				<Driven steps={[...OPEN, { wait: 800 }, { lose: true }]}>
					<Cam />
				</Driven>
			</Block>
			<Block caption="lost mid video: the take is kept">
				<Driven steps={[...RECORD, { wait: 1500 }, { lose: true }]}>
					<Cam mode="video" audio={false} />
				</Driven>
			</Block>
		</ThemePair>
	),
};

export const ReadOnly: StoryObj = {
	render: () => (
		<ThemePair>
			<Block caption="read only, a photo: shows, nothing else">
				<PhotoTake readOnly />
			</Block>
			<Block caption="read only, nothing taken">
				<Cam readOnly mode="video" />
			</Block>
		</ThemePair>
	),
};

export const Disabled: StoryObj = {
	render: () => (
		<ThemePair>
			<Block caption="disabled">
				<Cam disabled />
			</Block>
			<Block caption="disabled, a photo">
				<PhotoTake disabled />
			</Block>
		</ThemePair>
	),
};

const meta: Meta = {
	title: "UI/CameraCapture",
	parameters: sinkParameters,
};

export default meta;
