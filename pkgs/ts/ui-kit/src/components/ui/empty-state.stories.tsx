import type { Meta, StoryObj } from "@storybook/react-vite";
import { Inbox, Plus } from "lucide-react";
import { Button } from "./button";
import { EmptyState } from "./empty-state";
import { Spinner } from "./spinner";

const SIZES = ["sm", "md"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<EmptyState>Nothing here yet</EmptyState>
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
			{SIZES.map((s) => (
				<div key={s}>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						{s}
					</div>
					<div className="grid grid-cols-3 gap-4">
						<div className="rounded-md border border-border-subtle">
							<EmptyState size={s}>No planes inside</EmptyState>
						</div>
						<div className="rounded-md border border-border-subtle">
							<EmptyState
								size={s}
								icon={<Inbox />}
								description="Planes you create show up here"
								action={
									<Button variant="secondary" size="sm">
										<Plus />
										New plane
									</Button>
								}
							>
								No planes yet
							</EmptyState>
						</div>
						<div className="rounded-md border border-border-subtle">
							<EmptyState size={s} icon={<Spinner tone="neutral" label="Loading" />}>
								Loading
							</EmptyState>
						</div>
					</div>
				</div>
			))}
		</div>
	),
};

const meta: Meta = {
	title: "UI/EmptyState",
};

export default meta;
