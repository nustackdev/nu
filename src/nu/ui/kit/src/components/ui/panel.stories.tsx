import type { Meta, StoryObj } from "@storybook/react-vite";
import { Filter } from "lucide-react";
import { IconButton } from "./icon-button";
import {
	Panel,
	PanelContent,
	PanelDescription,
	PanelFooter,
	PanelHeader,
	PanelTitle,
} from "./panel";

const VARIANTS = ["default", "sunken", "elevated"] as const;
const SIZES = ["sm", "md", "lg"] as const;

function Sample({
	variant,
	size,
}: {
	variant?: "default" | "sunken" | "elevated";
	size?: "sm" | "md" | "lg";
}) {
	return (
		<Panel variant={variant} size={size}>
			<PanelHeader>
				<PanelTitle>Filters</PanelTitle>
				<div className="ml-auto">
					<IconButton variant="ghost" size="sm" aria-label="Filter">
						<Filter />
					</IconButton>
				</div>
			</PanelHeader>
			<PanelContent>
				<PanelDescription>Denser than Card. Toolbar-flavored.</PanelDescription>
				<div className="mt-3 text-sm text-text-primary">Panel body slot.</div>
			</PanelContent>
			<PanelFooter>
				<div className="text-xs text-text-muted">3 filters applied</div>
			</PanelFooter>
		</Panel>
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
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants
					</div>
					<div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
			</div>
	),
};

const meta: Meta = {
	title: "UI/Panel",
};

export default meta;
