import type { Meta, StoryObj } from "@storybook/react-vite";
import { Fragment } from "react";
import { ArrowRight, Sparkles, Github } from "lucide-react";
import { Button } from "./button";

const VARIANTS = ["default", "secondary", "ghost", "outline", "destructive", "link"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<Button>Button</Button>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants x sizes
					</div>
					<div className="grid grid-cols-[6rem_1fr] gap-4">
						<div />
						<div className="grid grid-flow-col auto-cols-fr gap-3">
							{SIZES.map((s) => (
								<div key={s} className="font-mono text-xs text-text-muted">
									{s}
								</div>
							))}
						</div>
						{VARIANTS.map((v) => (
							<Fragment key={v}>
								<div className="font-mono text-xs text-text-muted self-center">
									{v}
								</div>
								<div className="grid grid-flow-col auto-cols-fr gap-3 items-center">
									{SIZES.map((s) => (
										<div key={s}>
											<Button variant={v} size={s}>
												{v}
											</Button>
										</div>
									))}
								</div>
							</Fragment>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						states
					</div>
					<div className="flex flex-wrap gap-3">
						<Button>Default</Button>
						<Button disabled>Disabled</Button>
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						with icons
					</div>
					<div className="flex flex-wrap gap-3">
						<Button>
							<Sparkles />
							Leading
						</Button>
						<Button>
							Trailing
							<ArrowRight />
						</Button>
						<Button variant="outline">
							<Github />
							Both
							<ArrowRight />
						</Button>
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Button",
};

export default meta;
