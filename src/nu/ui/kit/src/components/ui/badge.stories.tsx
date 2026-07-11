import type { Meta, StoryObj } from "@storybook/react-vite";
import { Check, Circle, TriangleAlert } from "lucide-react";
import { Badge } from "./badge";

const VARIANTS = ["default", "secondary", "outline", "danger", "warn", "ok", "info"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<Badge>badge</Badge>
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
						{VARIANTS.map((v) => (
							<div key={v} className="flex items-center gap-3">
								<div className="w-20 font-mono text-xs text-text-muted">{v}</div>
								{SIZES.map((s) => (
									<Badge key={s} variant={v} size={s}>
										{v}
									</Badge>
								))}
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						with icons
					</div>
					<div className="flex flex-wrap gap-2">
						<Badge variant="ok">
							<Check />
							healthy
						</Badge>
						<Badge variant="warn">
							<TriangleAlert />
							attention
						</Badge>
						<Badge variant="danger">
							<Circle />
							down
						</Badge>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Badge",
};

export default meta;
