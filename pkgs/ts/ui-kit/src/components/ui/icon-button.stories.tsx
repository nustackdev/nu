import type { Meta, StoryObj } from "@storybook/react-vite";
import { Search, Star, Trash2 } from "lucide-react";
import { IconButton } from "./icon-button";

const VARIANTS = ["default", "secondary", "ghost", "outline", "destructive"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<IconButton aria-label="Search">
				<Search />
			</IconButton>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants x sizes
					</div>
					<div className="space-y-3">
						{VARIANTS.map((v) => (
							<div key={v} className="flex items-center gap-3">
								<div className="w-24 font-mono text-xs text-text-muted">{v}</div>
								{SIZES.map((s) => (
									<IconButton key={s} variant={v} size={s} aria-label={`${v} ${s}`}>
										<Star />
									</IconButton>
								))}
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="flex gap-3">
						<IconButton aria-label="Star">
							<Star />
						</IconButton>
						<IconButton disabled aria-label="Trash">
							<Trash2 />
						</IconButton>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/IconButton",
};

export default meta;
