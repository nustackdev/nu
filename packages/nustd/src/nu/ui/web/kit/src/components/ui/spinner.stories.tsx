import type { Meta, StoryObj } from "@storybook/react-vite";
import { Spinner } from "./spinner";

const SIZES = ["sm", "md", "lg", "xl"] as const;
const TONES = ["default", "neutral", "onSolid", "info", "danger", "warn", "ok"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Spinner />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="flex items-center gap-6">
						{SIZES.map((s) => (
							<div key={s} className="flex flex-col items-center gap-2">
								<Spinner size={s} />
								<div className="font-mono text-xs text-text-muted">{s}</div>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						tones
					</div>
					<div className="flex items-center gap-6">
						{TONES.map((t) => (
							<div
								key={t}
								className={
									t === "onSolid"
										? "flex flex-col items-center gap-2 rounded-md bg-accent p-3"
										: "flex flex-col items-center gap-2"
								}
							>
								<Spinner tone={t} />
								<div className="font-mono text-xs text-text-muted">{t}</div>
							</div>
						))}
					</div>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Spinner",
};

export default meta;
