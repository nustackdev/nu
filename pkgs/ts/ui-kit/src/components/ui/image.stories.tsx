import type { Meta, StoryObj } from "@storybook/react-vite";
import { Image } from "./image";

const SRC = "https://picsum.photos/seed/nu/400/240";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Image src={SRC} alt="Random landscape" aspectRatio="16 / 9" />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6 max-w-lg">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						radius
					</div>
					<div className="grid grid-cols-4 gap-3">
						{(["none", "sm", "md", "lg", "full"] as const).map((r) => (
							<div key={r}>
								<Image
									src={SRC}
									alt={`radius ${r}`}
									radius={r}
									aspectRatio="1 / 1"
									className="w-full"
								/>
								<div className="mt-1 text-center font-mono text-xs text-text-muted">
									{r}
								</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						fit
					</div>
					<div className="grid grid-cols-3 gap-3">
						{(["cover", "contain", "scale-down"] as const).map((f) => (
							<div key={f}>
								<Image
									src={SRC}
									alt={`fit ${f}`}
									fit={f}
									aspectRatio="1 / 1"
									className="w-full"
								/>
								<div className="mt-1 text-center font-mono text-xs text-text-muted">
									{f}
								</div>
							</div>
						))}
					</div>
				</div>
			</div>
	),
};

// Scroll the frame: each image is fetched only as it nears view
// (watch the network panel).
const LAZY_SEEDS = Array.from({ length: 30 }, (_, i) => `lazy${i + 1}`);

export const Lazy: StoryObj = {
	render: () => (
		<div className="m-8 h-96 max-w-md overflow-y-auto border border-border-default">
			<div className="space-y-6 p-4">
				{LAZY_SEEDS.map((seed, i) => (
					<div key={seed}>
						<Image
							src={`https://picsum.photos/seed/${seed}/400/240`}
							alt={`Lazy image ${i + 1}`}
							aspectRatio="5 / 3"
							className="w-full"
						/>
						<div className="mt-1 font-mono text-xs text-text-muted">{i + 1}</div>
					</div>
				))}
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Image",
};

export default meta;
