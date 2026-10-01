import type { Meta, StoryObj } from "@storybook/react-vite";
import { Kbd } from "./kbd";

const VARIANTS = ["default", "ghost"] as const;
const SIZES = ["sm", "md"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<Kbd>K</Kbd>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					variants x sizes
				</div>
				<div className="space-y-3">
					{VARIANTS.map((v) =>
						SIZES.map((s) => (
							<div key={`${v}-${s}`} className="flex items-center gap-2">
								<div className="w-24 font-mono text-xs text-text-muted">
									{v} {s}
								</div>
								<Kbd variant={v} size={s}>
									K
								</Kbd>
								<Kbd variant={v} size={s}>
									⌘
								</Kbd>
								<Kbd variant={v} size={s}>
									↵
								</Kbd>
								<Kbd variant={v} size={s}>
									Esc
								</Kbd>
								<Kbd variant={v} size={s}>
									Ctrl
								</Kbd>
							</div>
						)),
					)}
				</div>
			</div>

			<div>
				<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
					a single key in text
				</div>
				<p className="text-sm text-text-secondary">
					Press <Kbd>↵</Kbd> to search, <Kbd>Esc</Kbd> to close.
				</p>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Kbd",
};

export default meta;
