import type { Meta, StoryObj } from "@storybook/react-vite";
import { Skeleton } from "./skeleton";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Skeleton className="h-6 w-40" />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md space-y-6">
				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						shapes
					</div>
					<div className="flex items-center gap-3">
						<Skeleton className="h-8 w-8" shape="circle" />
						<div className="flex-1 space-y-1.5">
							<Skeleton shape="text" className="w-3/4" />
							<Skeleton shape="text" className="w-1/2" />
						</div>
					</div>
				</div>

				<div>
					<div className="mb-2 font-mono text-xs uppercase tracking-widest text-text-muted">
						card placeholder
					</div>
					<div className="rounded-md border border-border-subtle bg-bg-surface p-4 space-y-2">
						<Skeleton className="h-4 w-3/4" />
						<Skeleton className="h-3 w-1/2" />
						<Skeleton className="h-24 w-full" />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Skeleton",
};

export default meta;
