import type { Meta, StoryObj } from "@storybook/react-vite";
import { Home, Layers, Settings } from "lucide-react";
import { Badge } from "./badge";
import { NavLink } from "./nav-link";

const VARIANTS = ["default", "underline"] as const;
const SIZES = ["sm", "md", "lg"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-xs">
				<div className="flex flex-col gap-0.5">
					<NavLink href="#" active>
						<Home />
						Overview
					</NavLink>
					<NavLink href="#">
						<Layers />
						Traces
						<Badge variant="secondary" className="ml-auto">
							23
						</Badge>
					</NavLink>
					<NavLink href="#">
						<Settings />
						Settings
					</NavLink>
				</div>
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
					<div className="grid gap-6 md:grid-cols-2">
						{VARIANTS.map((v) => (
							<div key={v} className="w-56">
								<div className="mb-2 font-mono text-xs text-text-muted">{v}</div>
								<div className="flex flex-col gap-0.5">
									<NavLink href="#" variant={v}>
										<Home />
										Overview
									</NavLink>
									<NavLink href="#" variant={v} active>
										<Layers />
										Traces
									</NavLink>
									<NavLink href="#" variant={v}>
										<Settings />
										Settings
									</NavLink>
								</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="flex items-center gap-3">
						{SIZES.map((s) => (
							<NavLink key={s} href="#" size={s}>
								<Home />
								{s}
							</NavLink>
						))}
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/NavLink",
};

export default meta;
