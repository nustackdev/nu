// Refs/Capture: MicCaptureRef and CameraCaptureRef as Python sends them, over
// fake devices (lib/capture/fake-media.ts): real streams from a canvas and an
// oscillator, recorded by the browser's own MediaRecorder, so a take plays.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { type FakeMediaOptions, installFakeMedia } from "../../lib/capture/fake-media";
import { NodeStage, sinkParameters, step } from "./harness";

/** A story's `beforeEach`: fake devices while it shows, the browser's own back after. */
function fakeMedia(opts: FakeMediaOptions) {
	return () => {
		const media = installFakeMedia(opts);
		return () => media.restore();
	};
}

const meta: Meta = {
	title: "Refs/Capture",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

export const Mic: Story = {
	beforeEach: fakeMedia({ mics: 2, delayMs: 400 }),
	render: () => {
		const root = "capture-mic";
		return (
			<NodeStage
				root={root}
				label="MicCaptureRef: a voice memo up to 1:00; a music take with no voice cleanup, sm"
				chains={[
					[
						step(root, "Column", { gap: 4 }),
						step("memo", "MicCaptureRef", {
							label: "Voice memo",
							max_duration: 60,
							processing: true,
							required: true,
						}),
					],
					[
						step(root, "Column", { gap: 4 }),
						step("music", "MicCaptureRef", {
							label: "Room take",
							processing: false,
							size: "sm",
						}),
					],
				]}
			/>
		);
	},
};

export const Camera: Story = {
	beforeEach: fakeMedia({ cameras: 2, delayMs: 400 }),
	render: () => {
		const root = "capture-camera";
		return (
			<NodeStage
				root={root}
				label="CameraCaptureRef: a profile photo, webp, square; a back camera snapshot, sd, sm"
				chains={[
					[
						step(root, "Column", { gap: 4 }),
						step("profile", "CameraCaptureRef", {
							label: "Profile photo",
							format: "webp",
							aspect: "1/1",
							required: true,
						}),
					],
					[
						step(root, "Column", { gap: 4 }),
						step("snap", "CameraCaptureRef", {
							label: "Receipt",
							facing: "environment",
							resolution: "sd",
							size: "sm",
						}),
					],
				]}
			/>
		);
	},
};

export const CameraVideo: Story = {
	beforeEach: fakeMedia({ cameras: 2, delayMs: 400 }),
	render: () => {
		const root = "capture-camera-video";
		return (
			<NodeStage
				root={root}
				label="CameraCaptureRef mode=video: a clip up to 0:30 with sound; a silent one, fhd"
				chains={[
					[
						step(root, "Column", { gap: 4 }),
						step("clip", "CameraCaptureRef", {
							label: "Video answer",
							mode: "video",
							max_duration: 30,
						}),
					],
					[
						step(root, "Column", { gap: 4 }),
						step("silent", "CameraCaptureRef", {
							label: "Silent clip",
							mode: "video",
							audio: false,
							resolution: "fhd",
						}),
					],
				]}
			/>
		);
	},
};
