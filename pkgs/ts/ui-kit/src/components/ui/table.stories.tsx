import type { Meta, StoryObj } from "@storybook/react-vite";
import { Badge } from "./badge";
import {
	Table,
	TableBody,
	TableCaption,
	TableCell,
	TableFooter,
	TableHead,
	TableHeader,
	TableRow,
} from "./table";

const ROWS = [
	{ id: "run_142", model: "gpt-5", tokens: 1284, status: "ok" as const, latency: "820ms" },
	{ id: "run_141", model: "gpt-5-mini", tokens: 421, status: "ok" as const, latency: "180ms" },
	{ id: "run_140", model: "claude-4.7", tokens: 3120, status: "warn" as const, latency: "3.4s" },
	{ id: "run_139", model: "gpt-5", tokens: 640, status: "danger" as const, latency: "12.1s" },
];

const VARIANTS = ["default", "borderless", "striped"] as const;
const DENSITIES = ["compact", "default", "comfortable"] as const;

function Sample({
	variant,
	density,
}: {
	variant?: "default" | "borderless" | "striped";
	density?: "compact" | "default" | "comfortable";
}) {
	return (
		<Table variant={variant} density={density}>
			<TableHeader>
				<TableRow>
					<TableHead>Run</TableHead>
					<TableHead>Model</TableHead>
					<TableHead className="text-right">Tokens</TableHead>
					<TableHead>Status</TableHead>
					<TableHead className="text-right">Latency</TableHead>
				</TableRow>
			</TableHeader>
			<TableBody>
				{ROWS.map((r) => (
					<TableRow key={r.id}>
						<TableCell className="font-mono">{r.id}</TableCell>
						<TableCell>{r.model}</TableCell>
						<TableCell className="text-right font-mono">{r.tokens}</TableCell>
						<TableCell>
							<Badge variant={r.status}>{r.status}</Badge>
						</TableCell>
						<TableCell className="text-right font-mono">{r.latency}</TableCell>
					</TableRow>
				))}
			</TableBody>
			<TableFooter>
				<TableRow>
					<TableCell colSpan={2}>Total</TableCell>
					<TableCell className="text-right font-mono">
						{ROWS.reduce((s, r) => s + r.tokens, 0)}
					</TableCell>
					<TableCell colSpan={2} />
				</TableRow>
			</TableFooter>
			<TableCaption>4 runs in the last hour.</TableCaption>
		</Table>
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
		<div className="p-8 space-y-8">
				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						variants
					</div>
					<div className="space-y-6">
						{VARIANTS.map((v) => (
							<div key={v}>
								<div className="mb-2 font-mono text-xs text-text-muted">{v}</div>
								<Sample variant={v} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						densities
					</div>
					<div className="space-y-6">
						{DENSITIES.map((d) => (
							<div key={d}>
								<div className="mb-2 font-mono text-xs text-text-muted">{d}</div>
								<Sample density={d} />
							</div>
						))}
					</div>
				</div>

				<div>
					<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
						selected row
					</div>
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Name</TableHead>
								<TableHead>Kind</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							<TableRow>
								<TableCell>Row A</TableCell>
								<TableCell>Trace</TableCell>
							</TableRow>
							<TableRow selected>
								<TableCell>Row B</TableCell>
								<TableCell>Trace</TableCell>
							</TableRow>
							<TableRow>
								<TableCell>Row C</TableCell>
								<TableCell>Trace</TableCell>
							</TableRow>
						</TableBody>
					</Table>
				</div>
			</div>
	),
};

// Wider than its box: the table scrolls sideways inside its frame and the
// first column stays pinned, on a phone and in a narrow desktop column alike.
// Scrolled a little at load, so a still shows the pin.
const WIDE_COLUMNS = ["Run", "Model", "Tokens", "Status", "Latency", "Region", "Started"];

export const Wide: StoryObj = {
	render: () => (
		<div className="p-4">
			<Table variant="striped">
				<TableHeader>
					<TableRow>
						{WIDE_COLUMNS.map((c) => (
							<TableHead key={c}>{c}</TableHead>
						))}
					</TableRow>
				</TableHeader>
				<TableBody>
					{ROWS.map((r, i) => (
						<TableRow key={r.id} selected={i === 2}>
							<TableCell className="font-mono whitespace-nowrap">{r.id}</TableCell>
							<TableCell className="whitespace-nowrap">{r.model}</TableCell>
							<TableCell className="text-right font-mono">{r.tokens}</TableCell>
							<TableCell>
								<Badge variant={r.status}>{r.status}</Badge>
							</TableCell>
							<TableCell className="text-right font-mono">{r.latency}</TableCell>
							<TableCell className="whitespace-nowrap">eu-central-1</TableCell>
							<TableCell className="whitespace-nowrap font-mono">2026-11-27 18:4{i}</TableCell>
						</TableRow>
					))}
				</TableBody>
			</Table>
		</div>
	),
	play: async ({ canvasElement }) => {
		await new Promise((r) => setTimeout(r, 150));
		const frame = canvasElement.querySelector<HTMLElement>("[data-slot=table-frame]");
		if (frame) frame.scrollLeft = 100;
	},
};

const meta: Meta = {
	title: "UI/Table",
};

export default meta;
