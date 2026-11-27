import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { IconMark } from "./icon-mark";
import { IconPicker, IconPickerContent, IconPickerField } from "./icon-picker";
import { Popover, PopoverTrigger } from "./popover";

const SIZES = ["sm", "md", "lg"] as const;
const MARKS = ["lucide:rocket", "emoji:🌱", "FileText", "nope"] as const;

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<IconPickerField defaultValue="emoji:🌱" aria-label="Icon" />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					sizes
				</div>
				<div className="flex items-center gap-3">
					{SIZES.map((s) => (
						<IconPickerField
							key={s}
							size={s}
							defaultValue="lucide:rocket"
							aria-label={`Icon ${s}`}
						/>
					))}
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					states
				</div>
				<div className="flex items-center gap-3">
					<IconPickerField aria-label="Empty" />
					<IconPickerField defaultValue="emoji:🐱" invalid aria-label="Invalid" />
					<IconPickerField defaultValue="emoji:🐱" disabled aria-label="Disabled" />
					<IconPickerField
						kinds={["lucide"]}
						placeholder="Glyphs only"
						clearable={false}
						aria-label="Glyphs only"
					/>
				</div>
			</div>

			<div>
				<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
					marks: a glyph, an emoji, a bare name, junk with a fallback
				</div>
				{SIZES.map((s) => (
					<div key={s} className="mb-2 flex items-center gap-3 text-text-secondary">
						{MARKS.map((m) => (
							<IconMark key={m} icon={m} fallback="lucide:file-text" size={s} />
						))}
					</div>
				))}
			</div>
		</div>
	),
};

/** The caller owns the popover and its trigger: here a mark that changes on a pick. */
function OwnTrigger() {
	const [icon, setIcon] = useState("lucide:folder");
	const [open, setOpen] = useState(false);
	return (
		<Popover open={open} onOpenChange={setOpen}>
			<PopoverTrigger
				aria-label="Change icon"
				className="flex size-10 items-center justify-center rounded-md text-text-muted hover:bg-bg-hover"
			>
				<IconMark icon={icon} fallback="lucide:file-text" size="lg" />
			</PopoverTrigger>
			<IconPickerContent
				align="start"
				value={icon}
				recentKey="storybook.icons.recent"
				onPick={(v) => {
					setIcon(v);
					setOpen(false);
				}}
				onRemove={() => {
					setIcon("");
					setOpen(false);
				}}
			/>
		</Popover>
	);
}

export const CallerTrigger: StoryObj = {
	render: () => (
		<div className="p-8">
			<OwnTrigger />
		</div>
	),
};

/** The bare panel, as it sits inside the popover. */
export const Panel: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className="w-82 rounded-md border border-border-default bg-bg-elevated">
				<IconPicker value="lucide:cpu" onPick={() => {}} onRemove={() => {}} />
			</div>
		</div>
	),
};

// Opened at load: in touch mode the picker fills a bottom sheet with 44px
// cells, on desktop the anchored popover.
export const Open: StoryObj = {
	render: () => (
		<div className="p-8">
			<IconPickerField defaultValue="emoji:🌱" aria-label="Icon" />
		</div>
	),
	play: async ({ canvasElement }) => {
		canvasElement.querySelector<HTMLElement>('[data-slot="icon-picker-trigger"]')?.click();
	},
};

const meta: Meta = {
	title: "UI/IconPicker",
};

export default meta;
