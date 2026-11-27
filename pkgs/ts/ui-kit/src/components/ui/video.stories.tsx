import type { Meta, StoryObj } from "@storybook/react-vite";
import { Video } from "./video";

// CC0 clips MDN serves with open CORS.
const FLOWER = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4";
const FRIDAY = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/friday.mp4";
const POSTER = "https://picsum.photos/seed/nu-video/1280/720";

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
			<Video src={FLOWER} label="Flower" />
		</div>
	),
};

export const WithPoster: StoryObj = {
	render: () => (
		<div className="max-w-2xl p-8">
			<Video src={FRIDAY} poster={POSTER} aspectRatio="16 / 9" fit="cover" label="Friday" />
		</div>
	),
};

export const Frames: StoryObj = {
	render: () => (
		<div className="space-y-8 p-8">
			<div>
				<Label>small, square, cover</Label>
				<div className="w-56">
					<Video src={FLOWER} aspectRatio="1 / 1" fit="cover" radius="lg" label="Flower, square" />
				</div>
			</div>
			<div>
				<Label>wide, 21 / 9, contain</Label>
				<div className="max-w-4xl">
					<Video src={FRIDAY} aspectRatio="21 / 9" radius="sm" label="Friday, wide" />
				</div>
			</div>
			<div>
				<Label>no radius, loop, muted</Label>
				<div className="max-w-md">
					<Video src={FLOWER} radius="none" loop muted label="Flower, looping" />
				</div>
			</div>
		</div>
	),
};

export const States: StoryObj = {
	render: () => (
		<div className="grid max-w-4xl grid-cols-2 gap-6 p-8">
			<div>
				<Label>source fails</Label>
				<Video src="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/missing.mp4" />
			</div>
			<div>
				<Label>no source</Label>
				<Video />
			</div>
		</div>
	),
};

export const Autoplay: StoryObj = {
	render: () => (
		<div className="max-w-2xl p-8">
			<Label>autoplay needs muted in most browsers</Label>
			<Video src={FLOWER} autoPlay muted loop label="Flower, autoplay" />
		</div>
	),
};

/** Filling its column. In touch mode the transport stays up the whole time. */
export const Touch: StoryObj = {
	render: () => (
		<div className="p-4">
			<Video src={FLOWER} label="Flower" download={FLOWER} />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Video",
};

export default meta;
