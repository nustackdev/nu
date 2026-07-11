import type { Meta, StoryObj } from "@storybook/react-vite";
import { Text } from "./text";

const SIZES = ["xs", "sm", "base", "lg", "xl"] as const;
const TONES = ["primary", "secondary", "muted", "danger", "warn", "ok", "info", "accent"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Text>Body text sits at base by default.</Text>
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-6 max-w-lg">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						sizes
					</div>
					<div className="space-y-2">
						{SIZES.map((s) => (
							<div key={s} className="grid grid-cols-[4rem_1fr] items-baseline gap-3">
								<div className="font-mono text-xs text-text-muted">{s}</div>
								<Text size={s}>The quick brown fox jumps over the lazy dog</Text>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						tones
					</div>
					<div className="space-y-1.5">
						{TONES.map((t) => (
							<div key={t} className="grid grid-cols-[6rem_1fr] items-baseline gap-3">
								<div className="font-mono text-xs text-text-muted">{t}</div>
								<Text tone={t}>The quick brown fox jumps over the lazy dog</Text>
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						mono
					</div>
					<Text mono>const x = 42; // monospace text via `mono` prop</Text>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Text",
};

export default meta;
