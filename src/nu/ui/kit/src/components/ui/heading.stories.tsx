import type { Meta, StoryObj } from "@storybook/react-vite";
import { Heading } from "./heading";

const SIZES = ["display", "3xl", "2xl", "xl", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Heading>Section title</Heading>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-4">
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sizes
				</div>
				{SIZES.map((s) => (
					<div key={s} className="grid grid-cols-[6rem_1fr] items-baseline gap-4">
						<div className="font-mono text-xs text-text-muted">{s}</div>
						<Heading size={s} as="h2">
							The nu design system
						</Heading>
					</div>
				))}
			</div>
	),
};

const meta: Meta = {
	title: "UI/Heading",
};

export default meta;
