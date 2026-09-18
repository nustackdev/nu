import type { Meta, StoryObj } from "@storybook/react-vite";
import { Kbd } from "./kbd";

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
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						single keys
					</div>
					<div className="flex flex-wrap items-center gap-2">
						<Kbd>K</Kbd>
						<Kbd>Enter</Kbd>
						<Kbd>Esc</Kbd>
						<Kbd>Tab</Kbd>
						<Kbd>Space</Kbd>
					</div>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						combos
					</div>
					<div className="flex flex-wrap items-center gap-3">
						<span className="inline-flex items-center gap-1">
							<Kbd>⌘</Kbd>
							<span className="text-text-muted">+</span>
							<Kbd>K</Kbd>
						</span>
						<span className="inline-flex items-center gap-1">
							<Kbd>⇧</Kbd>
							<span className="text-text-muted">+</span>
							<Kbd>Enter</Kbd>
						</span>
						<span className="inline-flex items-center gap-1">
							<Kbd>Ctrl</Kbd>
							<span className="text-text-muted">+</span>
							<Kbd>⇧</Kbd>
							<span className="text-text-muted">+</span>
							<Kbd>P</Kbd>
						</span>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Kbd",
};

export default meta;
