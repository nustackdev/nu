// Kitchen sink: every table, light and dark side by side. The display Table in
// each variant and density, the DataTable read-only and fully live, and the
// markdown table, so the three share one row ladder at a glance.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import {
	DataTable,
	type DataTableColumn,
	type DataTableEdit,
	type DataTableRow,
	type DataTableSort,
} from "../../components/ui/data-table";
import { Markdown } from "../../components/ui/markdown";
import {
	Table,
	TableBody,
	TableCaption,
	TableCell,
	TableFooter,
	TableHead,
	TableHeader,
	TableRow,
} from "../../components/ui/table";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const VARIANTS = ["default", "borderless", "striped"] as const;
const DENSITIES = ["compact", "default", "comfortable"] as const;

const RUNS = [
	{ run: "ingest", status: "ok", label: "done", rows: "1,204" },
	{ run: "train", status: "warn", label: "slow", rows: "88" },
	{ run: "report", status: "danger", label: "failed", rows: "0" },
	{ run: "export", status: "info", label: "queued", rows: "512" },
] as const;

function DisplayTable({
	variant = "default",
	density = "default",
	selected,
	footer,
	caption,
}: {
	variant?: (typeof VARIANTS)[number];
	density?: (typeof DENSITIES)[number];
	selected?: number;
	footer?: boolean;
	caption?: boolean;
}) {
	return (
		<div className="w-full">
			<Table variant={variant} density={density}>
				{caption ? <TableCaption>Runs from the last hour.</TableCaption> : null}
				<TableHeader>
					<TableRow>
						<TableHead>Run</TableHead>
						<TableHead>Status</TableHead>
						<TableHead className="text-right">Rows</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{RUNS.map((r, i) => (
						<TableRow key={r.run} selected={i === selected}>
							<TableCell>{r.run}</TableCell>
							<TableCell>
								<Badge variant={r.status}>{r.label}</Badge>
							</TableCell>
							<TableCell className="text-right">{r.rows}</TableCell>
						</TableRow>
					))}
				</TableBody>
				{footer ? (
					<TableFooter>
						<TableRow>
							<TableCell>Total</TableCell>
							<TableCell />
							<TableCell className="text-right">1,804</TableCell>
						</TableRow>
					</TableFooter>
				) : null}
			</Table>
		</div>
	);
}

function Display() {
	return (
		<Block title="Table (display)">
			{VARIANTS.map((variant) => (
				<Row key={variant} label={variant}>
					<DisplayTable variant={variant} />
				</Row>
			))}
			{DENSITIES.map((density) => (
				<Row key={density} label={`density ${density}`}>
					<DisplayTable density={density} variant="striped" />
				</Row>
			))}
			<Row label="selected row">
				<DisplayTable selected={1} />
			</Row>
			<Row label="striped selected">
				<DisplayTable variant="striped" selected={1} />
			</Row>
			<Row label="footer, caption">
				<DisplayTable footer caption />
			</Row>
		</Block>
	);
}

const COLUMNS: DataTableColumn[] = [
	{ key: "name", label: "Name" },
	{ key: "runs", label: "Runs", kind: "number" },
	{ key: "live", label: "Live", kind: "bool" },
	{ key: "stage", label: "Stage", kind: "select", options: ["draft", "live", "done"] },
];

const ROWS: DataTableRow[] = [
	{ key: "a", cells: ["ingest", 128, true, "live"] },
	{ key: "b", cells: ["train", 42, false, "draft"] },
	{ key: "c", cells: ["report", 7, true, "done"] },
	{ key: "d", cells: ["export", 64, false, "live"] },
	{ key: "e", cells: ["archive", 3, false, "done"] },
];

/** A DataTable with every request answered in place, so each state is reachable. */
function LiveDataTable({
	striped,
	density,
	variant,
	editable = true,
}: {
	striped?: boolean;
	density?: (typeof DENSITIES)[number];
	variant?: "default" | "borderless";
	editable?: boolean;
}) {
	const [rows, setRows] = useState<DataTableRow[]>(ROWS);
	const [selected, setSelected] = useState<string[]>(["b"]);
	const [sort, setSort] = useState<DataTableSort>(null);
	const [next, setNext] = useState(0);

	const onSort = (column: string, direction: "asc" | "desc") => {
		const i = COLUMNS.findIndex((c) => c.key === column);
		const sign = direction === "asc" ? 1 : -1;
		setSort({ column, direction });
		setRows((rs) =>
			[...rs].sort((x, y) => (String(x.cells[i]) > String(y.cells[i]) ? sign : -sign)),
		);
	};
	const onEdit = (e: DataTableEdit) => {
		const i = COLUMNS.findIndex((c) => c.key === e.column);
		setRows((rs) =>
			rs.map((r) =>
				r.key === e.key ? { ...r, cells: r.cells.map((v, j) => (j === i ? e.value : v)) } : r,
			),
		);
	};
	const onAdd = (index: number) => {
		setNext((n) => n + 1);
		setRows((rs) => [
			...rs.slice(0, index),
			{ key: `new-${next}`, cells: ["", 0, false, "draft"] },
			...rs.slice(index),
		]);
	};
	const onDelete = (keys: string[]) => setRows((rs) => rs.filter((r) => !keys.includes(r.key)));
	const onMove = (key: string, index: number) =>
		setRows((rs) => {
			const row = rs.find((r) => r.key === key);
			if (!row) return rs;
			const rest = rs.filter((r) => r.key !== key);
			return [...rest.slice(0, index), row, ...rest.slice(index)];
		});

	return (
		<div className="w-full">
			<DataTable
				aria-label="Stages"
				columns={COLUMNS}
				rows={rows}
				striped={striped}
				density={density}
				variant={variant}
				selection="multi"
				selected={selected}
				onSelect={setSelected}
				sort={sort}
				onSort={onSort}
				onEdit={editable ? onEdit : undefined}
				onAdd={editable ? onAdd : undefined}
				onDelete={editable ? onDelete : undefined}
				onMove={editable ? onMove : undefined}
			/>
		</div>
	);
}

function Grid() {
	return (
		<Block title="DataTable">
			<Row label="read only">
				<LiveDataTable editable={false} />
			</Row>
			<Row label="live">
				<LiveDataTable />
			</Row>
			<Row label="striped">
				<LiveDataTable striped />
			</Row>
			<Row label="borderless">
				<LiveDataTable variant="borderless" />
			</Row>
			{DENSITIES.map((density) => (
				<Row key={density} label={`density ${density}`}>
					<LiveDataTable density={density} striped />
				</Row>
			))}
			<Row label="empty">
				<div className="w-full">
					<DataTable aria-label="Empty" columns={COLUMNS} rows={[]} />
				</div>
			</Row>
		</Block>
	);
}

const MD_TABLE = `| Run | Status | Rows |
| :-- | :-: | --: |
| ingest | done | 1,204 |
| train | slow | 88 |
| report | failed | 0 |
| export | queued | 512 |
`;

const MD_WIDE = `Planes resume after a restart. The runs from the last hour:

| Plane | Owner | Started | Retries | Note |
| --- | --- | --- | --: | --- |
| ingest | gor | 09:12 | 0 | \`nu demo\` source |
| train | david | 09:40 | 2 | **slow** on blue |
| report | gor | 10:05 | 1 | see the [log](#) |
`;

function MarkdownTables() {
	return (
		<Block title="Markdown table">
			<Row label="aligned">
				<Markdown value={MD_TABLE} className="w-full" />
			</Row>
			<Row label="in prose">
				<Markdown value={MD_WIDE} className="w-full" />
			</Row>
			<Row label="editable">
				<Markdown value={MD_TABLE} readOnly={false} className="w-full" />
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Tables",
	render: () => (
		<SinkPage
			title="Tables"
			description="The display Table, the DataTable and the markdown table, in every variant and density. The DataTables are live: hover, click, select, sort, edit, add, delete and drag."
		>
			<ThemePair>
				<Display />
				<Grid />
				<MarkdownTables />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Tables",
	parameters: sinkParameters,
};

export default meta;
