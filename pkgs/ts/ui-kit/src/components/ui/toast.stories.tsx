import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect } from "react";
import { Button } from "./button";
import { dismissToast, Toaster, type ToastTone, toast } from "./toast";

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

export const WithAction: StoryObj = {
	render: () => (
		<div className="p-8">
			<Button
				variant="secondary"
				onClick={() =>
					toast({ title: "3 cells deleted", action: { label: "Undo", onClick: () => {} } })
				}
			>
				delete
			</Button>
			<Toaster />
		</div>
	),
};

// A stack shown at load and kept up: bottom right on desktop, along the top
// edge under the notch in touch mode (a phone, or the Touch toolbar), the
// newest first.
function StackAtLoad() {
	useEffect(() => {
		const long = 10 * 60 * 1000;
		const ids = [
			toast({ tone: "ok", title: "Plane saved", duration: long }),
			toast({
				tone: "danger",
				title: "Refused",
				description: "plane home is a system plane",
				duration: long,
			}),
			toast({
				title: "3 cells deleted",
				action: { label: "Undo", onClick: () => {} },
				duration: long,
			}),
		];
		return () => {
			for (const id of ids) dismissToast(id);
		};
	}, []);
	return (
		<div className="p-8">
			<Button variant="secondary" onClick={() => toast({ title: "One more", tone: "info" })}>
				one more
			</Button>
			<Toaster />
		</div>
	);
}

export const Stack: StoryObj = {
	render: () => <StackAtLoad />,
};

const meta: Meta = {
	title: "UI/Toast",
};

export default meta;
