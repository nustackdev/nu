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

const WIDTHS = [384, 512, 672, 896] as const;

function Sample({ width }: { width?: number }) {
	return (
		<Dialog>
			<DialogTrigger asChild>
				<Button variant="secondary">Open {width ?? 512}px</Button>
			</DialogTrigger>
			<DialogContent width={width}>
				<DialogHeader>
					<DialogTitle>Delete project</DialogTitle>
					<DialogDescription>
						This action cannot be undone. Traces, dashboards, and cached runs under this project
						will be dropped.
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
			<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">widths</div>
			<div className="flex flex-wrap gap-3">
				{WIDTHS.map((w) => (
					<Sample key={w} width={w} />
				))}
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Dialog",
};

export default meta;
