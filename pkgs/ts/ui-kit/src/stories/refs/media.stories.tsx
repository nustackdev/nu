// Refs/Media: VideoRef and AudioRef as Python sends them. A video with a
// poster held to a ratio, a stack of audio rows, and the empty frames.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { NodeStage, sinkParameters, step } from "./harness";

const meta: Meta = {
	title: "Refs/Media",
	parameters: sinkParameters,
};

export default meta;

type Story = StoryObj;

const MDN = "https://interactive-examples.mdn.mozilla.net/media";

export const Video: Story = {
	render: () => {
		const root = "media-video";
		return (
			<NodeStage
				root={root}
				label="VideoRef: a poster, 16/9, md corners; then one with no source"
				chains={[
					[
						step(root, "Column", { gap: 4 }),
						step("clip", "VideoRef", {
							src: `${MDN}/cc0-videos/friday.mp4`,
							poster: "https://picsum.photos/seed/nu-video/1280/720",
							aspect: "16/9",
							radius: "md",
							fit: "cover",
						}),
					],
					[
						step(root, "Column", { gap: 4 }),
						step("empty", "VideoRef", { src: "", aspect: "21/9" }),
					],
				]}
			/>
		);
	},
};

export const Audio: Story = {
	render: () => {
		const root = "media-audio";
		return (
			<NodeStage
				root={root}
				label="AudioRef: rows in a column, a title each, one with no source"
				chains={[
					[
						step(root, "Column", { gap: 1 }),
						step("roar", "AudioRef", {
							src: `${MDN}/cc0-audio/t-rex-roar.mp3`,
							title: "t-rex-roar.mp3",
						}),
					],
					[
						step(root, "Column", { gap: 1 }),
						step("take", "AudioRef", {
							src: "https://samplelib.com/mp3/sample-9s.mp3",
							title: "sample-9s.mp3",
							loop: true,
						}),
					],
					[step(root, "Column", { gap: 1 }), step("none", "AudioRef", { title: "untitled.mp3" })],
				]}
			/>
		);
	},
};
