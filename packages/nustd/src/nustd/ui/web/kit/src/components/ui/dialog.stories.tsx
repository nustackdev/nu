import type { Meta, StoryObj } from "@storybook/react-vite";
import { Button } from "./button";
import {
	Dialog,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "./dialog";

const SIZES = ["sm", "md", "lg", "xl"] as const;

function Sample({ size }: { size?: "sm" | "md" | "lg" | "xl" }) {
	return (
		<Dialog>
			<DialogTrigger asChild>
				<Button variant="secondary">Open {size ?? "md"}</Button>
			</DialogTrigger>
			<DialogContent size={size}>
				<DialogHeader>
					<DialogTitle>Delete project</DialogTitle>
					<DialogDescription>
						This action cannot be undone. Traces, dashboards, and cached runs
						under this project will be dropped.
					</DialogDescription>
				</DialogHeader>
				<DialogFooter>
					<DialogClose asChild>
						<Button variant="secondary">Cancel</Button>
					</DialogClose>
					<DialogClose asChild>
						<Button variant="destructive">Delete</Button>
					</DialogClose>
				</DialogFooter>
			</DialogContent>
		</Dialog>
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
					sizes
				</div>
				<div className="flex flex-wrap gap-3">
					{SIZES.map((s) => (
						<Sample key={s} size={s} />
					))}
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/Dialog",
};

export default meta;
