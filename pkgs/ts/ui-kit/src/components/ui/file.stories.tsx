import type { Meta, StoryObj } from "@storybook/react-vite";
import { File } from "./file";

const meta: Meta<typeof File> = { title: "Primitives/File", component: File };
export default meta;

const SRC = "https://interactive-examples.mdn.mozilla.net/media/examples/lizard.png";

export const Default: StoryObj<typeof File> = {
	render: () => (
		<div className="max-w-md p-8">
			<File
				src={SRC}
				name="quarterly-report.pdf"
				size={2_480_113}
				mime="application/pdf"
				download={SRC}
			/>
		</div>
	),
};

export const Kinds: StoryObj<typeof File> = {
	render: () => (
		<div className="flex max-w-md flex-col gap-1 p-8">
			<File src={SRC} name="lizard.png" size={98_310} mime="image/png" download={SRC} />
			<File src={SRC} name="take-01.wav" size={12_400_000} mime="audio/wav" download={SRC} />
			<File src={SRC} name="clip.mp4" size={88_000_000} mime="video/mp4" download={SRC} />
			<File src={SRC} name="runs.csv" size={48_200} mime="text/csv" download={SRC} />
			<File src={SRC} name="config.json" size={812} mime="application/json" download={SRC} />
			<File
				src={SRC}
				name="weights.zip"
				size={1_204_000_000}
				mime="application/zip"
				download={SRC}
			/>
			<File
				src={SRC}
				name="a-very-long-file-name-that-has-to-truncate-somewhere-in-the-row.bin"
				size={10}
			/>
		</div>
	),
};

export const Empty: StoryObj<typeof File> = {
	render: () => (
		<div className="flex max-w-md flex-col gap-1 p-8">
			<File name="later.csv" />
			<File />
		</div>
	),
};
