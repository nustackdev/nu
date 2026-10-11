// Kitchen sink: the Line primitive, inline runs of text, links, badges, keys
// and dots wrapping like a paragraph, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { ExternalLink } from "lucide-react";
import { Badge } from "../../components/ui/badge";
import { Kbd } from "../../components/ui/kbd";
import { Line, lineChip, lineDot } from "../../components/ui/line";
import { Shortcut } from "../../components/ui/shortcut";
import { StatusDot } from "../../components/ui/status-dot";
import { Block, Row, SinkPage, sinkParameters, ThemePair } from "./frame";

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

function Runs() {
	return (
		<Block title="Runs">
			<Row label="sentence" className="block">
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
			</Row>
			<Row label="wraps" className="block">
				<Line>
					<StatusDot tone="warn" label="degraded" className={lineDot} />
					<Badge variant="warn" className={lineChip}>
						degraded
					</Badge>
					<span>{LONG}; press</span>
					<Kbd className={lineChip}>Esc</Kbd>
					<span>to dismiss.</span>
				</Line>
			</Row>
			<Row label="chips" className="block">
				<Line>
					<span>Tags</span>
					{(["default", "secondary", "outline", "ok", "warn", "danger", "dashed"] as const).map(
						(v) => (
							<Badge key={v} variant={v} className={lineChip}>
								{v}
							</Badge>
						),
					)}
					<span>and keys</span>
					<Kbd className={lineChip}>K</Kbd>
					<Kbd size="sm" className={lineChip}>
						Esc
					</Kbd>
					<Shortcut keys={["mod", "shift", "P"]} platform="mac" className={lineChip} />
					<Shortcut keys={["mod", "K"]} platform="other" variant="ghost" className={lineChip} />
				</Line>
			</Row>
		</Block>
	);
}

function Layout() {
	return (
		<Block title="Layout">
			{(["start", "center", "end"] as const).map((align) => (
				<Row key={align} label={`align ${align}`} className="block">
					<Line align={align}>
						<span>Synced</span>
						<Badge variant="ok" className={lineChip}>
							12 files
						</Badge>
						<span>just now</span>
					</Line>
				</Row>
			))}
			<Row label="wrap false" className="block">
				<Line wrap={false}>
					<Badge variant="info" className={lineChip}>
						note
					</Badge>
					<span>{LONG}</span>
				</Line>
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	parameters: sinkParameters,
	render: () => (
		<SinkPage
			title="Line"
			description="Inline runs of text, links, badges and keys, wrapping like a paragraph."
		>
			<ThemePair>
				<Runs />
				<Layout />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Layout/Line",
	parameters: sinkParameters,
};

export default meta;
