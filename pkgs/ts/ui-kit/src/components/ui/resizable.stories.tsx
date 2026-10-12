import type { Meta, StoryObj } from "@storybook/react-vite";
import { PanelLeft } from "lucide-react";
import { useRef } from "react";
import { IconButton } from "./icon-button";
import {
	ResizableHandle,
	ResizablePanel,
	ResizablePanelGroup,
	type ResizablePanelGroupHandle,
} from "./resizable";

function Pane({ label, tone = "bg-bg-surface" }: { label: string; tone?: string }) {
	return (
		<div className={`flex size-full items-center justify-center ${tone}`}>
			<span className="font-mono text-xs uppercase tracking-widest text-text-muted">{label}</span>
		</div>
	);
}

function Frame({ children }: { children: React.ReactNode }) {
	return (
		<div className="p-8">
			<div className="h-80 overflow-hidden rounded-md border border-border-default">{children}</div>
		</div>
	);
}

export const Default: StoryObj = {
	render: () => (
		<Frame>
			<ResizablePanelGroup>
				<ResizablePanel defaultSize={30} minSize={15}>
					<Pane label="one" />
				</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel minSize={15}>
					<Pane label="two" />
				</ResizablePanel>
			</ResizablePanelGroup>
		</Frame>
	),
};

export const Vertical: StoryObj = {
	render: () => (
		<Frame>
			<ResizablePanelGroup orientation="vertical">
				<ResizablePanel minSize="60px">
					<Pane label="top" />
				</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel minSize="60px">
					<Pane label="bottom" />
				</ResizablePanel>
			</ResizablePanelGroup>
		</Frame>
	),
};

/** Three columns, the middle one a vertical split: an editor-shaped layout. */
export const Nested: StoryObj = {
	render: () => (
		<Frame>
			<ResizablePanelGroup>
				<ResizablePanel defaultSize={22} minSize="140px" maxSize="320px">
					<Pane label="files" tone="bg-bg-sunken" />
				</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel minSize={30}>
					<ResizablePanelGroup orientation="vertical">
						<ResizablePanel defaultSize={70} minSize={20}>
							<Pane label="editor" />
						</ResizablePanel>
						<ResizableHandle />
						<ResizablePanel minSize="48px">
							<Pane label="terminal" tone="bg-bg-sunken" />
						</ResizablePanel>
					</ResizablePanelGroup>
				</ResizablePanel>
				<ResizableHandle />
				<ResizablePanel defaultSize={22} minSize={12}>
					<Pane label="outline" tone="bg-bg-sunken" />
				</ResizablePanel>
			</ResizablePanelGroup>
		</Frame>
	),
};

/**
 * A sidebar: a px default, so it holds 240px while the frame resizes and the
 * content takes the change. Drag it well below its minimum and it folds;
 * Enter on the focused handle, or the button, folds and unfolds it. The
 * layout, the fold and the width it unfolds to survive a reload; double-click
 * a handle to reset.
 */
function CollapsibleDemo() {
	const group = useRef<ResizablePanelGroupHandle>(null);
	return (
		<div className="p-8 space-y-3">
			<IconButton
				variant="ghost"
				size="sm"
				aria-label="Toggle sidebar"
				onClick={() => {
					const g = group.current;
					if (!g) return;
					if (g.isCollapsed(0)) g.expand(0);
					else g.collapse(0);
				}}
			>
				<PanelLeft />
			</IconButton>
			<div className="h-80 overflow-hidden rounded-md border border-border-default">
				<ResizablePanelGroup ref={group} storageKey="ui-kit.story.resizable">
					<ResizablePanel defaultSize="240px" minSize="160px" maxSize="400px" collapsible>
						<Pane label="sidebar" tone="bg-bg-sunken" />
					</ResizablePanel>
					<ResizableHandle />
					<ResizablePanel minSize={30}>
						<Pane label="content" />
					</ResizablePanel>
				</ResizablePanelGroup>
			</div>
		</div>
	);
}

export const Collapsible: StoryObj = {
	render: () => <CollapsibleDemo />,
};

/**
 * `overflow="scroll"`: four panels that never squeeze under 240px, so a
 * narrow frame scrolls sideways. Drag a border past its neighbour's minimum
 * and the content grows instead of the drag stopping.
 */
export const Desk: StoryObj = {
	render: () => (
		<Frame>
			<ResizablePanelGroup overflow="scroll">
				{["one", "two", "three", "four"].flatMap((label, i) => [
					i > 0 ? <ResizableHandle key={`h-${label}`} /> : null,
					<ResizablePanel key={label} id={`desk-${label}`} minSize="240px">
						<Pane label={label} />
					</ResizablePanel>,
				])}
			</ResizablePanelGroup>
		</Frame>
	),
};

const meta: Meta = {
	title: "UI/Resizable",
};

export default meta;
