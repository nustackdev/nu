import type { Meta, StoryObj } from "@storybook/react-vite";
import { Bold, Italic, Underline } from "lucide-react";
import { Toggle } from "./toggle";

const VARIANTS = ["default", "outline"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Toggle aria-label="Toggle bold">
					<Bold />
				</Toggle>
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
						{VARIANTS.map((v) => (
							<div key={v} className="flex items-center gap-3">
								<div className="w-20 font-mono text-xs text-text-muted">{v}</div>
								{SIZES.map((s) => (
									<Toggle key={s} variant={v} size={s} aria-label={`${v} ${s}`}>
										<Bold />
									</Toggle>
								))}
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states + label
					</div>
					<div className="flex gap-1">
						<Toggle aria-label="Bold">
							<Bold />
						</Toggle>
						<Toggle defaultPressed aria-label="Italic">
							<Italic />
						</Toggle>
						<Toggle disabled aria-label="Underline">
							<Underline />
						</Toggle>
						<Toggle aria-label="Wrap">Wrap</Toggle>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Toggle",
};

export default meta;
