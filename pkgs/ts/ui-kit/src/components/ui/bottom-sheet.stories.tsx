import type { Meta, StoryObj } from "@storybook/react-vite";
import { Copy, Pencil, RotateCw, Trash2 } from "lucide-react";
import {
	BottomSheet,
	BottomSheetContent,
	BottomSheetFooter,
	BottomSheetItem,
	BottomSheetTrigger,
} from "./bottom-sheet";
import { Button } from "./button";
import { Input } from "./input";

// The touch-mode surface. Bottom sheets look the same on any device, so these
// stories open on desktop too; the kit only reaches for them in touch mode.

export const Actions: StoryObj = {
	render: () => (
		<div className="p-8">
			<BottomSheet defaultOpen>
				<BottomSheetTrigger asChild>
					<Button variant="secondary">Cell actions</Button>
				</BottomSheetTrigger>
				<BottomSheetContent title="deploy-api">
					<BottomSheetItem>
						<RotateCw />
						Restart
					</BottomSheetItem>
					<BottomSheetItem>
						<Copy />
						Copy id
					</BottomSheetItem>
					<BottomSheetItem>
						<Pencil />
						Rename
					</BottomSheetItem>
					<BottomSheetItem variant="danger">
						<Trash2 />
						Delete
					</BottomSheetItem>
				</BottomSheetContent>
			</BottomSheet>
		</div>
	),
};

export const Options: StoryObj = {
	render: () => (
		<div className="p-8">
			<BottomSheet defaultOpen>
				<BottomSheetTrigger asChild>
					<Button variant="secondary">env</Button>
				</BottomSheetTrigger>
				<BottomSheetContent label="env">
					{["dev", "staging", "prod"].map((env) => (
						<BottomSheetItem key={env} selected={env === "prod"}>
							{env}
						</BottomSheetItem>
					))}
				</BottomSheetContent>
			</BottomSheet>
		</div>
	),
};

export const Form: StoryObj = {
	render: () => (
		<div className="p-8">
			<BottomSheet defaultOpen>
				<BottomSheetTrigger asChild>
					<Button variant="secondary">Rename plane</Button>
				</BottomSheetTrigger>
				<BottomSheetContent title="Rename plane">
					<Input defaultValue="deploys" aria-label="Name" />
					<BottomSheetFooter>
						<Button>Save</Button>
						<Button variant="secondary">Cancel</Button>
					</BottomSheetFooter>
				</BottomSheetContent>
			</BottomSheet>
		</div>
	),
};

export const LongList: StoryObj = {
	render: () => (
		<div className="p-8">
			<BottomSheet defaultOpen>
				<BottomSheetTrigger asChild>
					<Button variant="secondary">Timezone</Button>
				</BottomSheetTrigger>
				<BottomSheetContent title="Timezone">
					{Array.from({ length: 27 }, (_, i) => `UTC${i >= 12 ? "+" : ""}${i - 12}:00`).map(
						(tz) => (
							<BottomSheetItem key={tz}>{tz}</BottomSheetItem>
						),
					)}
				</BottomSheetContent>
			</BottomSheet>
		</div>
	),
};

const meta: Meta = {
	title: "UI/BottomSheet",
};
export default meta;
