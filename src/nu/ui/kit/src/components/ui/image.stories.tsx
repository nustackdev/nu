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
						{(["none", "sm", "md", "lg"] as const).map((r) => (
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

const meta: Meta = {
	title: "UI/Image",
};

export default meta;
