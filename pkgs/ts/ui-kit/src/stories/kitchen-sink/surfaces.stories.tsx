// Kitchen sink: containers, type and data displays, light and dark side by side.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { MoreHorizontal } from "lucide-react";
import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "../../components/ui/card";
import { Code } from "../../components/ui/code";
import { DataTable, type DataTableColumn, type DataTableRow } from "../../components/ui/data-table";
import { Heading } from "../../components/ui/heading";
import { IconButton } from "../../components/ui/icon-button";
import { Image } from "../../components/ui/image";
import { JsonView } from "../../components/ui/json-view";
import { List, ListItem } from "../../components/ui/list";
import { Markdown } from "../../components/ui/markdown";
import {
	Panel,
	PanelContent,
	PanelDescription,
	PanelFooter,
	PanelHeader,
	PanelTitle,
} from "../../components/ui/panel";
import { Section } from "../../components/ui/section";
import { Separator } from "../../components/ui/separator";
import { Stat, StatDelta, StatLabel, StatValue } from "../../components/ui/stat";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "../../components/ui/table";
import { Text } from "../../components/ui/text";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const CARD_VARIANTS = ["default", "elevated", "sunken", "outline"] as const;
const PANEL_VARIANTS = ["default", "elevated", "sunken"] as const;
const HEADING_SIZES = ["display", "3xl", "2xl", "xl", "lg"] as const;
const TONES = ["primary", "secondary", "muted", "accent", "info", "ok", "warn", "danger"] as const;
const TEXT_SIZES = ["xs", "sm", "base", "lg", "xl"] as const;

const MARKDOWN = `## Release notes

Planes now **resume** after a restart. See the [changelog](#) for details.

- Faster cold start
- \`examples/\` ships two new apps

> Quoted: a calm line of context.

| Run | Status |
| --- | --- |
| a1 | done |
`;

const PYTHON = `from nu import ref

@ref
def total(xs: list[int]) -> int:
    # sum, but tracked
    return sum(xs) + 1`;

const JSON_SAMPLE = {
	id: "run-42",
	ok: true,
	score: 0.97,
	tags: ["nu", "kit"],
	owner: null,
	meta: { started: "2026-10-11", retries: 2 },
};

const DT_COLUMNS: DataTableColumn[] = [
	{ key: "name", label: "Name" },
	{ key: "runs", label: "Runs", kind: "number" },
	{ key: "live", label: "Live", kind: "bool" },
	{ key: "stage", label: "Stage", kind: "select", options: ["draft", "live", "done"] },
];
const DT_ROWS: DataTableRow[] = [
	{ key: "a", cells: ["ingest", 128, true, "live"] },
	{ key: "b", cells: ["train", 42, false, "draft"] },
	{ key: "c", cells: ["report", 7, true, "done"] },
];

// A tiny inline SVG so Image needs no network.
const IMAGE_SRC = `data:image/svg+xml;utf8,${encodeURIComponent(
	'<svg xmlns="http://www.w3.org/2000/svg" width="160" height="90"><defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#6d5bd0"/><stop offset="1" stop-color="#4f8bd6"/></linearGradient></defs><rect width="160" height="90" fill="url(#g)"/></svg>',
)}`;

function Containers() {
	return (
		<Block title="Containers">
			<Row label="Card" className="items-stretch">
				{CARD_VARIANTS.map((variant) => (
					<Card key={variant} variant={variant} className="w-52">
						<CardHeader>
							<CardTitle>{variant}</CardTitle>
							<CardDescription>Card description.</CardDescription>
							<CardAction>
								<IconButton variant="ghost" size="sm" aria-label="More">
									<MoreHorizontal />
								</IconButton>
							</CardAction>
						</CardHeader>
						<CardContent>
							<Text size="sm">Body copy sits here.</Text>
						</CardContent>
						<CardFooter>
							<Button size="sm" variant="secondary">
								Open
							</Button>
						</CardFooter>
					</Card>
				))}
				<Card interactive className="w-52">
					<CardHeader>
						<CardTitle>interactive</CardTitle>
						<CardDescription>Hover for the border.</CardDescription>
					</CardHeader>
					<CardContent className="pb-4" />
				</Card>
			</Row>
			<Row label="Panel" className="items-stretch">
				{PANEL_VARIANTS.map((variant) => (
					<Panel key={variant} variant={variant} className="w-52">
						<PanelHeader>
							<PanelTitle>{variant}</PanelTitle>
						</PanelHeader>
						<PanelContent>
							<PanelDescription>Dense inspector content.</PanelDescription>
						</PanelContent>
						<PanelFooter>
							<Button size="sm" variant="ghost">
								Reset
							</Button>
						</PanelFooter>
					</Panel>
				))}
			</Row>
			<Row label="Section">
				<Section
					className="w-full"
					bordered
					title="Planes"
					description="Every plane in this space."
					actions={<Button size="sm">New plane</Button>}
				>
					<Text size="sm" tone="secondary">
						Section body.
					</Text>
				</Section>
			</Row>
			<Row label="Separator">
				<div className="flex w-full flex-col gap-4">
					<Separator />
					<Separator label="or" />
					<div className="flex h-6 items-center gap-3">
						<Text as="span" size="sm">
							Left
						</Text>
						<Separator orientation="vertical" />
						<Text as="span" size="sm">
							Right
						</Text>
					</div>
				</div>
			</Row>
		</Block>
	);
}

function Type() {
	return (
		<Block title="Type">
			<Row label="Heading" className="flex-col items-start gap-1">
				{HEADING_SIZES.map((size) => (
					<Heading key={size} as="h3" size={size}>
						Heading {size}
					</Heading>
				))}
			</Row>
			<Row label="Text tones">
				{TONES.map((tone) => (
					<Text key={tone} as="span" tone={tone}>
						{tone}
					</Text>
				))}
			</Row>
			<Row label="Text sizes">
				{TEXT_SIZES.map((size) => (
					<Text key={size} as="span" size={size}>
						{size}
					</Text>
				))}
				<Text as="span" mono>
					mono
				</Text>
				<Text as="span" weight="semibold">
					semibold
				</Text>
			</Row>
			<Row label="Markdown">
				<Markdown className="w-full" value={MARKDOWN} />
			</Row>
			<Row label="Code inline">
				<Text as="span" size="sm">
					Run <Code>python examples/movies.py</Code> to start.
				</Text>
			</Row>
			<Row label="Code block">
				<Code block copyable language="python" className="w-full" value={PYTHON} />
			</Row>
			<Row label="JsonView">
				<JsonView value={JSON_SAMPLE} />
			</Row>
			<Row label="List">
				<List>
					<ListItem>Bullet one</ListItem>
					<ListItem>Bullet two</ListItem>
				</List>
				<List variant="number">
					<ListItem>Number one</ListItem>
					<ListItem>Number two</ListItem>
				</List>
			</Row>
		</Block>
	);
}

function Data() {
	return (
		<Block title="Data">
			<Row label="Table">
				<div className="w-full">
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Run</TableHead>
								<TableHead>Status</TableHead>
								<TableHead className="text-right">Rows</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							<TableRow>
								<TableCell>ingest</TableCell>
								<TableCell>
									<Badge variant="ok">done</Badge>
								</TableCell>
								<TableCell className="text-right">1,204</TableCell>
							</TableRow>
							<TableRow selected>
								<TableCell>train (selected)</TableCell>
								<TableCell>
									<Badge variant="warn">slow</Badge>
								</TableCell>
								<TableCell className="text-right">88</TableCell>
							</TableRow>
							<TableRow>
								<TableCell>report</TableCell>
								<TableCell>
									<Badge variant="danger">failed</Badge>
								</TableCell>
								<TableCell className="text-right">0</TableCell>
							</TableRow>
						</TableBody>
					</Table>
				</div>
			</Row>
			<Row label="Table striped">
				<div className="w-full">
					<Table variant="striped" density="compact">
						<TableHeader>
							<TableRow>
								<TableHead>Key</TableHead>
								<TableHead>Value</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{["alpha", "beta", "gamma", "delta"].map((k, i) => (
								<TableRow key={k}>
									<TableCell>{k}</TableCell>
									<TableCell>{i * 17}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</div>
			</Row>
			<Row label="DataTable">
				<div className="w-full">
					<DataTable
						aria-label="Stages"
						columns={DT_COLUMNS}
						rows={DT_ROWS}
						selection="multi"
						selected={["b"]}
						onSelect={() => {}}
						sort={{ column: "runs", direction: "desc" }}
						onSort={() => {}}
					/>
				</div>
			</Row>
			<Row label="Image">
				<Image src={IMAGE_SRC} alt="Gradient sample" className="w-40" aspectRatio="16 / 9" />
				<Image src={IMAGE_SRC} alt="Gradient sample" radius="lg" className="w-24" aspectRatio="1 / 1" />
			</Row>
			<Row label="Avatar">
				{(["sm", "md", "lg", "xl"] as const).map((size) => (
					<Avatar key={size} size={size}>
						<AvatarFallback>GM</AvatarFallback>
					</Avatar>
				))}
			</Row>
			<Row label="Stat">
				<Stat>
					<StatLabel>Runs</StatLabel>
					<StatValue>1,284</StatValue>
					<StatDelta direction="up">12%</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Errors</StatLabel>
					<StatValue>17</StatValue>
					<StatDelta direction="down" invert>
						4%
					</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Latency</StatLabel>
					<StatValue>212ms</StatValue>
					<StatDelta direction="up" invert>
						8%
					</StatDelta>
				</Stat>
				<Stat>
					<StatLabel>Flat</StatLabel>
					<StatValue>3</StatValue>
					<StatDelta>0%</StatDelta>
				</Stat>
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Surfaces",
	render: () => (
		<SinkPage title="Surfaces" description="Containers, type and data displays.">
			<ThemePair>
				<Containers />
				<Type />
				<Data />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Surfaces",
	parameters: sinkParameters,
};

export default meta;
