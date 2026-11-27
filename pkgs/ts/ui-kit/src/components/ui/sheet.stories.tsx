import type { Meta, StoryObj } from "@storybook/react-vite";
import { Badge } from "./badge";
import { Button } from "./button";
import {
	Sheet,
	SheetClose,
	SheetContent,
	SheetDescription,
	SheetFooter,
	SheetHeader,
	SheetTitle,
	SheetTitleBox,
	SheetTrigger,
} from "./sheet";
import { StatusDot } from "./status-dot";

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
						Slide-in drawer built on Radix Dialog. Same focus trap and Esc semantics.
					</SheetDescription>
				</SheetHeader>
			</SheetContent>
		</Sheet>
	);
}

// A header line in place of the string title: SheetTitleBox still names the
// sheet by its text, and lets a one-line name inside it truncate.
function HeaderSample() {
	return (
		<Sheet>
			<SheetTrigger asChild>
				<Button variant="secondary">Open with header box</Button>
			</SheetTrigger>
			<SheetContent>
				<SheetHeader className="pr-8">
					<SheetTitleBox>
						<div className="flex min-w-0 items-center gap-2">
							<StatusDot tone="ok" />
							<span className="min-w-0 flex-1 truncate font-semibold text-text-primary">
								web-03.eu-central.cluster.internal, rebuilt from main
							</span>
							<Badge>primary</Badge>
						</div>
					</SheetTitleBox>
					<SheetDescription>4 vCPU, 16 GB, up 12 days.</SheetDescription>
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
			<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">sides</div>
			<div className="flex flex-wrap gap-3">
				{SIDES.map((s) => (
					<Sample key={s} side={s} />
				))}
			</div>
			<div className="mt-8 mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
				header box
			</div>
			<HeaderSample />
		</div>
	),
};

// Opened at load: in touch mode (a phone, or the Touch toolbar) a side
// sheet takes the whole width and stacks its actions; on desktop the 440px
// drawer.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8">
			<Sheet defaultOpen>
				<SheetTrigger asChild>
					<Button variant="secondary">Open sheet</Button>
				</SheetTrigger>
				<SheetContent>
					<SheetHeader>
						<SheetTitle>Edit host</SheetTitle>
						<SheetDescription>Changes apply on the next deploy.</SheetDescription>
					</SheetHeader>
					<div className="text-sm text-text-secondary">web-03, 4 vCPU, 16 GB, up 12 days.</div>
					<SheetFooter>
						<SheetClose asChild>
							<Button variant="secondary">Cancel</Button>
						</SheetClose>
						<SheetClose asChild>
							<Button>Save</Button>
						</SheetClose>
					</SheetFooter>
				</SheetContent>
			</Sheet>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Sheet",
};

export default meta;
