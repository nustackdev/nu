import type { Meta, StoryObj } from "@storybook/react-vite";
import { ExternalLink } from "lucide-react";
import { Badge } from "./badge";
import { Kbd } from "./kbd";
import { Line, lineChip, lineDot } from "./line";
import { Shortcut } from "./shortcut";
import { StatusDot } from "./status-dot";

const LONG =
	"the plane keeps every write it has seen since the last snapshot and replays them in order when it comes back, so nothing a reader saw goes missing";

function NuLink() {
	return (
		<a href="https://nustack.dev" className="text-accent-2 underline-offset-2 hover:underline">
			Nu
			<ExternalLink aria-hidden="true" className="ms-1 inline size-3.5 align-[-0.125em]" />
		</a>
	);
}

function Sentence() {
	return (
		<Line>
			<span>Built with</span>
			<NuLink />
			<Badge variant="info" className={lineChip}>
				0.6
			</Badge>
			<span>and ready: press</span>
			<Shortcut keys={["mod", "K"]} platform="mac" className={lineChip} />
			<span>to search, status</span>
			<StatusDot tone="ok" label="live" className={lineDot} />
			<span>live.</span>
		</Line>
	);
}

function Label({ children }: { children: string }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="max-w-md p-8">
			<Sentence />
		</div>
	),
};

export const Wrapping: StoryObj = {
	render: () => (
		<div className="space-y-8 p-8">
			{[480, 320, 200].map((w) => (
				<div key={w} style={{ width: w }}>
					<Label>{`${w}px`}</Label>
					<Line>
						<span>Status</span>
						<StatusDot tone="warn" label="degraded" className={lineDot} />
						<Badge variant="warn" className={lineChip}>
							degraded
						</Badge>
						<span>{LONG}</span>
						<Kbd className={lineChip}>Esc</Kbd>
						<span>dismisses.</span>
					</Line>
				</div>
			))}
		</div>
	),
};

export const AlignAndWrap: StoryObj = {
	render: () => (
		<div className="max-w-md space-y-6 p-8">
			{(["start", "center", "end"] as const).map((align) => (
				<div key={align}>
					<Label>{`align ${align}`}</Label>
					<Line align={align} className="border border-border-subtle border-dashed">
						<span>Synced</span>
						<Badge variant="ok" className={lineChip}>
							12 files
						</Badge>
						<span>just now</span>
					</Line>
				</div>
			))}
			<div>
				<Label>wrap false</Label>
				<Line wrap={false}>
					<Badge variant="info" className={lineChip}>
						note
					</Badge>
					<span>{LONG}</span>
				</Line>
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Line",
};

export default meta;
