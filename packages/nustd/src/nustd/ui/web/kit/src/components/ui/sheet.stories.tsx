import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
	SheetTrigger,
} from "./sheet";

const SIDES = ["right", "left", "top", "bottom"] as const;

function Sample({ side }: { side?: "right" | "left" | "top" | "bottom" }) {
	return (
		<Sheet>
			<SheetTrigger asChild>
				<Button variant="secondary">Open {side ?? "right"}</Button>
			</SheetTrigger>
			<SheetContent side={side}>
				<SheetHeader>
					<SheetTitle>Sheet from {side ?? "right"}</SheetTitle>
					<SheetDescription>
						Slide-in drawer built on Radix Dialog. Same focus trap and Esc
						semantics.
					</SheetDescription>
				</SheetHeader>
			</SheetContent>
		</Sheet>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
				<Sample />
			</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8">
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sides
				</div>
				<div className="flex flex-wrap gap-3">
					{SIDES.map((s) => (
						<Sample key={s} side={s} />
					))}
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Sheet",
};

export default meta;
