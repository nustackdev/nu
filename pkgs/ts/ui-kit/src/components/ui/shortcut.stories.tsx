import type { Meta, StoryObj } from "@storybook/react-vite";
import { PanelLeft, Search } from "lucide-react";
import { IconButton } from "./icon-button";
import { Shortcut } from "./shortcut";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./tooltip";

const COMBOS: string[][] = [
	["mod", "K"],
	["mod", "\\"],
	["mod", "enter"],
	["shift", "mod", "P"],
	["alt", "shift", "F"],
	["esc"],
	["G", "D"],
	["up"],
];

const label = "mb-3 font-mono text-xs uppercase tracking-widest text-text-muted";

export const Default: StoryObj = {
	render: () => (
		<div className="p-8">
			<Shortcut keys={["mod", "K"]} />
		</div>
	),
};

export const Platforms: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className={label}>key names, spelled per platform</div>
			<div className="grid grid-cols-[10rem_repeat(4,auto)] items-center gap-x-6 gap-y-3">
				<div />
				<div className="font-mono text-xs text-text-muted">mac</div>
				<div className="font-mono text-xs text-text-muted">mac ghost</div>
				<div className="font-mono text-xs text-text-muted">other</div>
				<div className="font-mono text-xs text-text-muted">other ghost</div>
				{COMBOS.map((keys) => (
					<div key={keys.join("+")} className="contents">
						<div className="font-mono text-xs text-text-muted">{JSON.stringify(keys)}</div>
						<Shortcut keys={keys} platform="mac" />
						<Shortcut keys={keys} platform="mac" variant="ghost" />
						<Shortcut keys={keys} platform="other" />
						<Shortcut keys={keys} platform="other" variant="ghost" />
					</div>
				))}
			</div>
		</div>
	),
};

export const Sizes: StoryObj = {
	render: () => (
		<div className="p-8 space-y-3">
			{(["sm", "md"] as const).map((s) => (
				<div key={s} className="flex items-center gap-4">
					<div className="w-12 font-mono text-xs text-text-muted">{s}</div>
					<Shortcut keys={["mod", "K"]} size={s} />
					<Shortcut keys={["shift", "mod", "P"]} size={s} />
					<Shortcut keys={["mod", "K"]} size={s} variant="ghost" />
				</div>
			))}
		</div>
	),
};

/** Where each variant goes: a chip that stands apart, ghost text beside a label. */
export const InContext: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8">
			<div>
				<div className={label}>tooltip (default, sm)</div>
				<TooltipProvider>
					<Tooltip open>
						<TooltipTrigger asChild>
							<IconButton variant="ghost" aria-label="Collapse sidebar">
								<PanelLeft />
							</IconButton>
						</TooltipTrigger>
						<TooltipContent side="right">
							<span className="inline-flex items-center gap-2">
								Collapse sidebar
								<Shortcut keys={["mod", "\\"]} size="sm" />
							</span>
						</TooltipContent>
					</Tooltip>
				</TooltipProvider>
			</div>

			<div>
				<div className={label}>search entry (default)</div>
				<button
					type="button"
					className="flex h-8 w-64 items-center gap-2 rounded-md bg-text-primary/6 px-2 text-text-muted"
				>
					<Search className="size-4" />
					<span className="flex-1 text-left text-sm">Search</span>
					<Shortcut keys={["mod", "K"]} />
				</button>
			</div>

			<div>
				<div className={label}>menu rows (ghost)</div>
				<div className="w-64 rounded-md border border-border-subtle bg-bg-elevated p-1">
					{[
						["Duplicate", ["mod", "D"]],
						["Rename", ["mod", "shift", "R"]],
						["Move to", ["mod", "shift", "P"]],
					].map(([name, keys]) => (
						<div
							key={name as string}
							className="flex h-8 items-center rounded-sm px-2 text-sm text-text-primary hover:bg-text-primary/8"
						>
							{name as string}
							<Shortcut keys={keys as string[]} variant="ghost" className="ml-auto" />
						</div>
					))}
				</div>
			</div>

			<div>
				<div className={label}>inline hint (default)</div>
				<p className="flex items-center gap-1.5 text-xs text-text-muted">
					unsaved
					<Shortcut keys={["mod", "enter"]} size="sm" />
					to run
				</p>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Shortcut",
};

export default meta;
