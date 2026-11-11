import type { Meta, StoryObj } from "@storybook/react-vite";
import { useRef } from "react";
import { Button } from "./button";
import { ScrollArea } from "./scroll-area";

const ROWS = Array.from({ length: 60 }, (_, i) => `Row ${i + 1}`);

function Label({ children }: { children: React.ReactNode }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

export const Vertical: StoryObj = {
	render: () => (
		<div className="p-8">
			<ScrollArea className="h-72 w-64 rounded-md border border-border-default bg-bg-surface">
				<div className="p-3 space-y-2">
					{ROWS.map((row) => (
						<div key={row} className="text-sm text-text-primary">
							{row}
						</div>
					))}
				</div>
			</ScrollArea>
		</div>
	),
};

export const Horizontal: StoryObj = {
	render: () => (
		<div className="p-8">
			<ScrollArea
				orientation="horizontal"
				className="w-96 rounded-md border border-border-default bg-bg-surface"
			>
				<div className="flex gap-2 p-3">
					{ROWS.slice(0, 24).map((row) => (
						<div
							key={row}
							className="shrink-0 rounded-sm border border-border-subtle px-3 py-2 text-sm text-text-primary"
						>
							{row}
						</div>
					))}
				</div>
			</ScrollArea>
		</div>
	),
};

export const Both: StoryObj = {
	render: () => (
		<div className="p-8">
			<ScrollArea
				orientation="both"
				className="h-72 w-96 rounded-md border border-border-default bg-bg-surface"
			>
				<div className="grid w-[64rem] grid-cols-8 gap-2 p-3">
					{Array.from({ length: 200 }, (_, i) => (
						<div
							// biome-ignore lint/suspicious/noArrayIndexKey: static grid
							key={i}
							className="rounded-sm border border-border-subtle px-2 py-1 font-mono text-xs text-text-secondary"
						>
							{`r${Math.floor(i / 8)} c${i % 8}`}
						</div>
					))}
				</div>
			</ScrollArea>
		</div>
	),
};

// A sidebar sized box: long rows truncate instead of pushing the area wide.
export const Sidebar: StoryObj = {
	render: () => (
		<div className="p-8">
			<div className="flex h-96 w-[252px] flex-col rounded-md border border-border-default bg-bg-canvas">
				<div className="shrink-0 border-b border-border-subtle px-3 py-2 text-sm text-text-secondary">
					Header
				</div>
				<ScrollArea className="min-h-0 flex-1">
					<div className="flex flex-col p-1.5">
						{ROWS.map((row) => (
							<div
								key={row}
								className="flex h-7 items-center rounded-sm px-2 text-sm text-text-secondary hover:bg-bg-hover"
							>
								<span className="truncate">
									{row}, a plane with a long title that does not fit the sidebar
								</span>
							</div>
						))}
					</div>
				</ScrollArea>
				<div className="shrink-0 border-t border-border-subtle px-3 py-2 text-sm text-text-secondary">
					Footer
				</div>
			</div>
		</div>
	),
};

// A strip of wide cards, with the viewport reached through `viewportRef` to
// scroll a card into view and to step the strip sideways.
function StripDemo() {
	const viewport = useRef<HTMLDivElement>(null);
	const cards = Array.from({ length: 8 }, (_, i) => `Column ${i + 1}`);
	const reveal = (i: number) =>
		viewport.current
			?.querySelector(`[data-card="${i}"]`)
			?.scrollIntoView({ inline: "nearest", block: "nearest", behavior: "smooth" });
	const step = (by: number) => viewport.current?.scrollBy({ left: by, behavior: "smooth" });
	return (
		<div className="p-8">
			<Label>viewportRef</Label>
			<div className="mb-3 flex flex-wrap gap-2">
				<Button size="sm" variant="secondary" onClick={() => step(-400)}>
					Left
				</Button>
				<Button size="sm" variant="secondary" onClick={() => step(400)}>
					Right
				</Button>
				<Button size="sm" variant="secondary" onClick={() => reveal(0)}>
					First
				</Button>
				<Button size="sm" variant="secondary" onClick={() => reveal(cards.length - 1)}>
					Last
				</Button>
			</div>
			<ScrollArea
				orientation="horizontal"
				viewportRef={viewport}
				className="h-80 w-full max-w-3xl rounded-md bg-bg-sunken"
			>
				<div className="flex h-80 gap-1.5 p-1.5">
					{cards.map((card, i) => (
						<div
							key={card}
							data-card={i}
							className="flex w-[500px] shrink-0 flex-col rounded-lg border border-border-subtle bg-bg-surface"
						>
							<div className="border-b border-border-subtle px-3 py-2 text-sm text-text-primary">
								{card}
							</div>
							<ScrollArea className="min-h-0 flex-1">
								<div className="space-y-1 p-3">
									{ROWS.map((row) => (
										<div key={row} className="text-sm text-text-secondary">
											{row}
										</div>
									))}
								</div>
							</ScrollArea>
						</div>
					))}
				</div>
			</ScrollArea>
		</div>
	);
}

export const Strip: StoryObj = {
	render: () => <StripDemo />,
};

// `scrollbar-thin` on a native scroller the kit does not own.
export const NativeThin: StoryObj = {
	render: () => (
		<div className="p-8">
			<Label>scrollbar-thin</Label>
			<pre className="scrollbar-thin h-48 w-96 overflow-auto rounded-md border border-border-default bg-bg-sunken p-3 font-mono text-xs text-text-secondary">
				{Array.from(
					{ length: 40 },
					(_, i) =>
						`${String(i + 1).padStart(3, "0")}  INFO  worker ${i % 4} picked job ${1000 + i} from the queue, payload ok, took ${(i * 7) % 90}ms`,
				).join("\n")}
			</pre>
		</div>
	),
};

const meta: Meta = {
	title: "UI/ScrollArea",
};

export default meta;
