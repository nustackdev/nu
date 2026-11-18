import type { Meta, StoryObj } from "@storybook/react-vite";
import { Badge } from "./badge";
import { Button } from "./button";
import {
	Dialog,
	DialogClose,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTitleBox,
	DialogTrigger,
} from "./dialog";
import { StatusDot } from "./status-dot";

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

// A header line in place of the string title: DialogTitleBox still names the
// dialog by its text, and lets a one-line name inside it truncate.
function HeaderSample() {
	return (
		<Dialog>
			<DialogTrigger asChild>
				<Button variant="secondary">Open with header box</Button>
			</DialogTrigger>
			<DialogContent width={420}>
				<DialogHeader className="pr-8">
					<DialogTitleBox>
						<div className="flex min-w-0 items-center gap-2">
							<StatusDot tone="warn" />
							<span className="min-w-0 flex-1 truncate text-lg font-semibold text-text-primary">
								Deploy web-03.eu-central.cluster.internal
							</span>
							<Badge variant="warn">prod</Badge>
						</div>
					</DialogTitleBox>
					<DialogDescription>Rolls out to 4 hosts, one at a time.</DialogDescription>
				</DialogHeader>
				<DialogFooter>
					<DialogClose asChild>
						<Button variant="secondary">Cancel</Button>
					</DialogClose>
					<DialogClose asChild>
						<Button>Deploy</Button>
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
			<div className="mt-8 mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
				header box
			</div>
			<HeaderSample />
		</div>
	),
};

const meta: Meta = {
	title: "UI/Dialog",
};

export default meta;
