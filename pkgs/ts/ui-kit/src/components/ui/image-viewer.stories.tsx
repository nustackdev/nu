import type { Meta, StoryObj } from "@storybook/react-vite";
import { type ReactNode, useState } from "react";
import { Button } from "./button";
import { ImageViewer } from "./image-viewer";

// Zoom and pan inside a fixed frame. Wheel or pinch to zoom toward the
// pointer, drag to pan, double click to toggle fit, + - 0 1 and the arrows
// once the frame has focus.

const PHOTO = "https://picsum.photos/seed/nu/1600/1000";
const LARGE = "https://picsum.photos/seed/nu-large/4000/2667";
// A 32px photo: the size of a model's input, where every pixel matters.
const SAMPLE = "https://picsum.photos/seed/nu-sample/32/32";

// A 16x16 sprite, inline so it needs no network. Past 1:1 it draws with
// hard pixels instead of a blur.
const SPRITE =
	"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAYUlEQVR42mMQE5EjCTEgcxaVvAEi/CIMaAZgaiBsAybCrgEuh6YUTQ8DfrMx7WFAdisepTg1YIYjdg1YwxHTx1g0EBtx/t3XCCJ0DfgNxq7hw4evQISsDi5CDQ2k+YF4BADnc+BhOjdhNAAAAABJRU5ErkJggg==";

function Caption({ children }: { children: ReactNode }) {
	return (
		<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<ImageViewer
				src={PHOTO}
				alt="Landscape"
				radius="md"
				className="w-[640px] border border-border-subtle"
				style={{ height: 400 }}
			/>
		</div>
	),
};

/** A 16px sprite fitted to the frame and zoomed with hard pixels. The readout names the pixel. */
export const PixelArt: StoryObj = {
	render: () => (
		<div className="p-8">
			<ImageViewer
				src={SPRITE}
				alt="Pixel sprite"
				pixel
				radius="md"
				className="w-[400px] border border-border-subtle"
				style={{ height: 400 }}
			/>
		</div>
	),
};

/** A model-sized input next to the same frame: low res stays legible when zoomed. */
export const LowRes: StoryObj = {
	render: () => (
		<div className="flex gap-6 p-8">
			<div>
				<Caption>32 x 32, fitted</Caption>
				<ImageViewer
					src={SAMPLE}
					alt="32 pixel sample"
					pixel
					className="w-[320px] border border-border-subtle"
					aspectRatio="1 / 1"
				/>
			</div>
			<div>
				<Caption>16 x 16, fitted</Caption>
				<ImageViewer
					src={SPRITE}
					alt="Pixel sprite"
					pixel
					className="w-[320px] border border-border-subtle"
					aspectRatio="1 / 1"
				/>
			</div>
		</div>
	),
};

/** A 4000px photo: fits down, then double click goes to 1:1 where you point. */
export const HighRes: StoryObj = {
	render: () => (
		<div className="p-8">
			<ImageViewer
				src={LARGE}
				alt="Large landscape"
				radius="md"
				className="w-[720px] border border-border-subtle"
				aspectRatio="16 / 9"
			/>
		</div>
	),
};

/** The cluster on hover (and focus), pinned, and gone. */
export const Controls: StoryObj = {
	render: () => (
		<div className="grid grid-cols-3 gap-6 p-8">
			{(["hover", "always", "none"] as const).map((controls) => (
				<div key={controls}>
					<Caption>{controls}</Caption>
					<ImageViewer
						src={PHOTO}
						alt={`Controls ${controls}`}
						controls={controls}
						className="border border-border-subtle"
						aspectRatio="4 / 3"
					/>
				</div>
			))}
		</div>
	),
};

/** The same viewer over the whole window. Esc or the close button returns. */
export const Fullscreen: StoryObj = {
	render: function Render() {
		const [open, setOpen] = useState(true);
		return (
			<div className="flex flex-col items-start gap-4 p-8">
				<Button variant="secondary" onClick={() => setOpen(true)}>
					Open fullscreen
				</Button>
				<ImageViewer
					src={LARGE}
					alt="Large landscape"
					pixel
					expanded={open}
					onExpandedChange={setOpen}
					className="w-[480px] border border-border-subtle"
					aspectRatio="3 / 2"
				/>
			</div>
		);
	},
};

/**
 * Filling its column, the way a phone or a narrow desk column shows it. In
 * touch mode the cluster is always up (nothing hovers), two fingers pinch,
 * one pans once zoomed, a double tap toggles fit.
 */
export const Touch: StoryObj = {
	render: () => (
		<div className="p-4">
			<ImageViewer
				src={PHOTO}
				alt="Landscape"
				radius="md"
				download={PHOTO}
				className="border border-border-subtle"
				aspectRatio="4 / 3"
			/>
		</div>
	),
};

const meta: Meta = {
	title: "UI/ImageViewer",
};

export default meta;
