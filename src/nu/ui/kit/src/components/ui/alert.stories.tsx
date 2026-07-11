import type { Meta, StoryObj } from "@storybook/react-vite";
import { Alert, AlertDescription, AlertIcon, AlertTitle } from "./alert";

const TONES = ["neutral", "info", "ok", "warn", "danger"] as const;

function Sample({ tone }: { tone?: "neutral" | "info" | "ok" | "warn" | "danger" }) {
	return (
		<Alert tone={tone}>
			<AlertIcon />
			<div>
				<AlertTitle>Alert title</AlertTitle>
				<AlertDescription>
					Explanatory body copy. Two lines maximum in most contexts.
				</AlertDescription>
			</div>
		</Alert>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-lg">
				<Sample tone="info" />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 max-w-lg space-y-3">
				{TONES.map((t) => (
					<Sample key={t} tone={t} />
				))}
			</div>
	),
};

const meta: Meta = {
	title: "UI/Alert",
};

export default meta;
