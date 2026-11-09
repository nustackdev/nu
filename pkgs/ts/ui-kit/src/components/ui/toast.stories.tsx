import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import { type ToastTone, Toaster, toast } from "./toast";

const TONES: ToastTone[] = ["neutral", "info", "ok", "warn", "danger"];

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 flex flex-wrap gap-2">
			{TONES.map((tone) => (
				<Button
					key={tone}
					variant="secondary"
					onClick={() =>
						toast({
							tone,
							title: tone === "danger" ? "Refused" : `A ${tone} notice`,
							description:
								tone === "danger" ? "plane home is a system plane" : "Something happened, briefly.",
						})
					}
				>
					{tone}
				</Button>
			))}
			<Toaster />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Toast",
};

export default meta;
