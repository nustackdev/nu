import type { Meta, StoryObj } from "@storybook/react-vite";
import { MoreHorizontal } from "lucide-react";
import { Button } from "./button";
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "./card";
import { IconButton } from "./icon-button";

const VARIANTS = ["default", "elevated", "sunken", "outline"] as const;
const SIZES = ["sm", "md", "lg"] as const;

function Sample({
	variant,
	size,
	interactive,
}: {
	variant?: "default" | "elevated" | "sunken" | "outline";
	size?: "sm" | "md" | "lg";
	interactive?: boolean;
}) {
	return (
		<Card variant={variant} size={size} interactive={interactive}>
			<CardHeader>
				<CardTitle>Card title</CardTitle>
				<CardDescription>Short supporting description.</CardDescription>
				<CardAction>
					<IconButton variant="ghost" size="sm" aria-label="More">
						<MoreHorizontal />
					</IconButton>
				</CardAction>
			</CardHeader>
			<CardContent>
				<div className="text-sm text-text-primary">
					Card body sits between the header and footer.
				</div>
			</CardContent>
			<CardFooter>
				<Button size="sm" variant="secondary">
					Cancel
				</Button>
				<Button size="sm">Save</Button>
			</CardFooter>
		</Card>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
				<Sample />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants
					</div>
					<div className="grid grid-cols-1 gap-4 md:grid-cols-2">
						{VARIANTS.map((v) => (
							<Sample key={v} variant={v} />
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="grid grid-cols-1 gap-4 md:grid-cols-3">
						{SIZES.map((s) => (
							<Sample key={s} size={s} />
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						interactive
					</div>
					<div className="max-w-md">
						<Sample interactive />
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Card",
};

export default meta;
