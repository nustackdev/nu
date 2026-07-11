import type { Meta, StoryObj } from "@storybook/react-vite";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./tabs";

const VARIANTS = ["line", "pill", "segmented"] as const;
const SIZES = ["sm", "md", "lg"] as const;

function Sample({
	variant,
	size,
}: {
	variant?: "line" | "pill" | "segmented";
	size?: "sm" | "md" | "lg";
}) {
	return (
		<Tabs defaultValue="one">
			<TabsList variant={variant}>
				<TabsTrigger size={size} variant={variant} value="one">
					Overview
				</TabsTrigger>
				<TabsTrigger size={size} variant={variant} value="two">
					Traces
				</TabsTrigger>
				<TabsTrigger size={size} variant={variant} value="three">
					Config
				</TabsTrigger>
			</TabsList>
			<TabsContent value="one">
				<div className="p-3 text-sm text-text-primary">Overview content.</div>
			</TabsContent>
			<TabsContent value="two">
				<div className="p-3 text-sm text-text-primary">Traces content.</div>
			</TabsContent>
			<TabsContent value="three">
				<div className="p-3 text-sm text-text-primary">Config content.</div>
			</TabsContent>
		</Tabs>
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
		<div className="p-8 space-y-8 max-w-2xl">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants
					</div>
					<div className="space-y-6">
						{VARIANTS.map((v) => (
							<div key={v}>
								<div className="mb-2 font-mono text-xs text-text-muted">{v}</div>
								<Sample variant={v} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes (line variant)
					</div>
					<div className="space-y-6">
						{SIZES.map((s) => (
							<div key={s}>
								<div className="mb-2 font-mono text-xs text-text-muted">{s}</div>
								<Sample size={s} />
							</div>
						))}
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Tabs",
};

export default meta;
