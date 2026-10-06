import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect, useRef, useState } from "react";
import {
	DataTable,
	type DataTableColumn,
	type DataTableEdit,
	type DataTableKind,
	type DataTableRow,
	type DataTableSort,
} from "./data-table";
import { Text } from "./text";

// In-memory hosts that take the table's intents the way an app would: the kit
// reports, the host applies (or refuses), the table redraws from what comes
// back. The Server confirm story puts a delay and a few refusals in between.
// Columns the same: a column request comes back as new columns, and new rows
// whose cells moved with them (cells here are by position).

const COLUMNS: DataTableColumn[] = [
	{ key: "id", label: "ID", editable: false, width: "5rem" },
	{ key: "title", label: "Title" },
	{ key: "points", label: "Points", kind: "number", width: "6rem" },
	{ key: "done", label: "Done", kind: "bool", width: "5rem" },
	{ key: "state", label: "State", kind: "select", options: ["todo", "doing", "review", "done"] },
];

const SEED: DataTableRow[] = [
	{ key: "t1", cells: ["T-1", "Ship the grid", 8, false, "doing"] },
	{ key: "t2", cells: ["T-2", "Write the stories", 3, true, "done"] },
	{ key: "t3", cells: ["T-3", "Wire TableRef", 5, false, "todo"] },
	{ key: "t4", cells: ["T-4", "Drag to reorder", 2, false, "review"] },
	{ key: "t5", cells: ["T-5", "Dark theme pass", 1, true, "done"] },
];

// --- What a host does with each intent -------------------------------------

let made = 0;

function blank(columns: readonly DataTableColumn[], key: string): DataTableRow {
	return {
		key,
		cells: columns.map((c, i) =>
			i === 0
				? key.toUpperCase()
				: c.kind === "number"
					? 0
					: c.kind === "bool"
						? false
						: c.kind === "select"
							? (c.options?.[0] ?? "")
							: "",
		),
	};
}

function edited(
	rows: readonly DataTableRow[],
	e: DataTableEdit,
	columns: readonly DataTableColumn[],
) {
	const at = columns.findIndex((c) => c.key === e.column);
	return rows.map((r) =>
		r.key === e.key ? { ...r, cells: r.cells.map((v, i) => (i === at ? e.value : v)) } : r,
	);
}

function added(rows: readonly DataTableRow[], index: number, columns: readonly DataTableColumn[]) {
	made += 1;
	const next = [...rows];
	next.splice(index, 0, blank(columns, `n-${made}`));
	return next;
}

function moved(rows: readonly DataTableRow[], key: string, index: number) {
	const row = rows.find((r) => r.key === key);
	const rest = rows.filter((r) => r.key !== key);
	if (row) rest.splice(index, 0, row);
	return rest;
}

function sorted(
	rows: readonly DataTableRow[],
	columns: readonly DataTableColumn[],
	column: string,
	direction: "asc" | "desc",
) {
	const at = columns.findIndex((c) => c.key === column);
	const sign = direction === "asc" ? 1 : -1;
	return [...rows].sort((a, b) => {
		const x = a.cells[at];
		const y = b.cells[at];
		if (typeof x === "number" && typeof y === "number") return (x - y) * sign;
		return String(x).localeCompare(String(y)) * sign;
	});
}

// --- What a host does with each column request -------------------------------

type Table = { columns: readonly DataTableColumn[]; rows: readonly DataTableRow[] };
type Align = "left" | "center" | "right";

let madeColumns = 0;

/** Every row's cells reshaped the way the columns were. */
function cellsBy(rows: readonly DataTableRow[], fn: (cells: unknown[]) => unknown[]) {
	return rows.map((r) => ({ ...r, cells: fn([...r.cells]) }));
}

function columnAdded(t: Table, index: number): Table {
	madeColumns += 1;
	const column: DataTableColumn = { key: `c-${madeColumns}`, label: `Column ${madeColumns}` };
	const columns = [...t.columns];
	columns.splice(index, 0, column);
	return { columns, rows: cellsBy(t.rows, (c) => [...c.slice(0, index), "", ...c.slice(index)]) };
}

function columnDeleted(t: Table, key: string): Table {
	const at = t.columns.findIndex((c) => c.key === key);
	if (at < 0) return t;
	return {
		columns: t.columns.filter((c) => c.key !== key),
		rows: cellsBy(t.rows, (c) => c.filter((_, i) => i !== at)),
	};
}

function columnMoved(t: Table, key: string, index: number): Table {
	const at = t.columns.findIndex((c) => c.key === key);
	const column = t.columns[at];
	if (!column) return t;
	const columns = t.columns.filter((c) => c.key !== key);
	columns.splice(index, 0, column);
	const rows = cellsBy(t.rows, (c) => {
		const [v] = c.splice(at, 1);
		c.splice(index, 0, v);
		return c;
	});
	return { columns, rows };
}

function columnChanged(t: Table, key: string, change: Partial<DataTableColumn>): Table {
	return { ...t, columns: t.columns.map((c) => (c.key === key ? { ...c, ...change } : c)) };
}

/** A cell read as another kind: a number parsed, a bool from its truth, else its text. */
function asKind(v: unknown, kind: DataTableKind): unknown {
	if (kind === "number") {
		const n = Number(v);
		return typeof v === "boolean" ? Number(v) : Number.isFinite(n) && v !== "" ? n : 0;
	}
	if (kind === "bool")
		return v === true || v === "true" || v === "yes" || (typeof v === "number" && v !== 0);
	return v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v);
}

function columnKinded(t: Table, key: string, kind: DataTableKind): Table {
	const at = t.columns.findIndex((c) => c.key === key);
	if (at < 0) return t;
	const rows = cellsBy(t.rows, (c) => c.map((v, i) => (i === at ? asKind(v, kind) : v)));
	const values = [...new Set(rows.map((r) => String(r.cells[at] ?? "")).filter((v) => v !== ""))];
	const options = kind === "select" ? (values.length ? values : ["one", "two"]) : undefined;
	return { rows, columns: columnChanged(t, key, { kind, options, align: undefined }).columns };
}

/** The six column callbacks over one table state, applied as they come (or `wrap`ped). */
function columnOps(
	set: (fn: (t: Table) => Table) => void,
	log: (text: string) => void,
	wrap: (what: string, refuse: (t: Table) => string | null, fn: (t: Table) => Table) => void = (
		what,
		_refuse,
		fn,
	) => {
		set(fn);
		log(what);
	},
) {
	return {
		onColumnAdd: (index: number) =>
			wrap(
				`add column at ${index}`,
				() => null,
				(t) => columnAdded(t, index),
			),
		onColumnDelete: (key: string) =>
			wrap(
				`delete column ${key}`,
				(t) => (t.columns.length <= 1 ? "the table keeps at least one column" : null),
				(t) => columnDeleted(t, key),
			),
		onColumnRename: (key: string, label: string) =>
			wrap(
				`rename ${key} to "${label}"`,
				() => (label.trim() === "" ? "a column needs a name" : null),
				(t) => columnChanged(t, key, { label: label.trim() }),
			),
		onColumnMove: (key: string, index: number) =>
			wrap(
				`move column ${key} to ${index}`,
				() => null,
				(t) => columnMoved(t, key, index),
			),
		onColumnKind: (key: string, kind: DataTableKind) =>
			wrap(
				`column ${key} as ${kind}`,
				() => null,
				(t) => columnKinded(t, key, kind),
			),
		onColumnAlign: (key: string, align: Align) =>
			wrap(
				`align ${key} ${align}`,
				() => null,
				(t) => columnChanged(t, key, { align }),
			),
	};
}

const frame = "p-8 max-w-3xl space-y-3";

// --- Default -----------------------------------------------------------------

/** Read-only: no callbacks, so nothing edits; still one tab stop with arrows inside. */
function ReadOnly() {
	return (
		<div className={frame}>
			<DataTable aria-label="Tasks" columns={COLUMNS} rows={SEED} />
		</div>
	);
}

// --- Playground --------------------------------------------------------------

type Args = {
	selection: "none" | "single" | "multi";
	editable: boolean;
	addable: boolean;
	deletable: boolean;
	movable: boolean;
	sortable: boolean;
	activatable: boolean;
	columnsEditable: boolean;
	density: "compact" | "default" | "comfortable";
	striped: boolean;
	variant: "default" | "borderless";
};

function PlaygroundHost(args: Args) {
	const [table, setTable] = useState<Table>({ columns: COLUMNS, rows: SEED });
	const { columns, rows } = table;
	const setRows = (fn: (rows: readonly DataTableRow[]) => readonly DataTableRow[]) =>
		setTable((t) => ({ ...t, rows: fn(t.rows) }));
	const [selected, setSelected] = useState<string[]>([]);
	const [sort, setSort] = useState<DataTableSort>(null);
	const [log, setLog] = useState(
		"Click a cell, then the keyboard: arrows, Enter, F2, Space, Delete",
	);
	const ops = columnOps(setTable, setLog);
	return (
		<div className={frame}>
			<DataTable
				aria-label="Tasks"
				columns={columns}
				rows={rows}
				density={args.density}
				striped={args.striped}
				variant={args.variant}
				selection={args.selection}
				selected={selected}
				onSelect={(keys) => {
					setSelected(keys);
					setLog(`select [${keys.join(", ")}]`);
				}}
				onActivate={
					args.activatable ? (key, index) => setLog(`activate ${key} (row ${index})`) : undefined
				}
				sort={sort}
				onSort={
					args.sortable
						? (column, direction) => {
								setSort({ column, direction });
								setRows((prev) => sorted(prev, columns, column, direction));
								setLog(`sort ${column} ${direction}`);
							}
						: undefined
				}
				onEdit={
					args.editable
						? (e) => {
								setRows((prev) => edited(prev, e, columns));
								setLog(`edit ${e.key}.${e.column}: ${String(e.previous)} -> ${String(e.value)}`);
							}
						: undefined
				}
				onAdd={
					args.addable
						? (index) => {
								setRows((prev) => added(prev, index, columns));
								setLog(`add at ${index}`);
							}
						: undefined
				}
				onDelete={
					args.deletable
						? (keys) => {
								setRows((prev) => prev.filter((r) => !keys.includes(r.key)));
								setSelected((prev) => prev.filter((k) => !keys.includes(k)));
								setLog(`delete [${keys.join(", ")}]`);
							}
						: undefined
				}
				onMove={
					args.movable
						? (key, index) => {
								setRows((prev) => moved(prev, key, index));
								setSort(null);
								setLog(`move ${key} -> ${index}`);
							}
						: undefined
				}
				{...(args.columnsEditable ? ops : {})}
			/>
			<Text size="xs" tone="muted" mono>
				{log}
			</Text>
		</div>
	);
}

// --- Server confirm ----------------------------------------------------------

const DELAY = 400;

/**
 * A fake server: every intent goes out, waits, and comes back applied or
 * refused. The table shows the old value until the answer lands. It refuses an
 * empty title, a negative number, deleting the last row, deleting the last
 * column and a rename to an empty name.
 */
function ServerHost() {
	const [table, setTable] = useState<Table>({ columns: COLUMNS, rows: SEED });
	const { columns, rows } = table;
	const setRows = (fn: (rows: readonly DataTableRow[]) => readonly DataTableRow[]) =>
		setTable((t) => ({ ...t, rows: fn(t.rows) }));
	const [selected, setSelected] = useState<string[]>([]);
	const [sort, setSort] = useState<DataTableSort>(null);
	const [status, setStatus] = useState<{ text: string; tone: "muted" | "ok" | "danger" }>({
		text: "Edits go to a fake server and land after a short delay.",
		tone: "muted",
	});
	const live = useRef(rows);
	live.current = rows;
	const liveTable = useRef(table);
	liveTable.current = table;
	// Answers still in flight die with the story.
	const timers = useRef(new Set<ReturnType<typeof setTimeout>>());
	useEffect(() => {
		const pendingTimers = timers.current;
		return () => {
			for (const id of pendingTimers) clearTimeout(id);
			pendingTimers.clear();
		};
	}, []);

	const ask = (what: string, answer: () => string | null, apply: () => void) => {
		setStatus({ text: `${what}: waiting for the server`, tone: "muted" });
		const id = setTimeout(() => {
			timers.current.delete(id);
			const refusal = answer();
			if (refusal) {
				setStatus({ text: `${what}: refused, ${refusal}`, tone: "danger" });
				return;
			}
			apply();
			setStatus({ text: `${what}: applied`, tone: "ok" });
		}, DELAY);
		timers.current.add(id);
	};

	const ops = columnOps(
		setTable,
		() => {},
		(what, refuse, fn) =>
			ask(
				what,
				() => refuse(liveTable.current),
				() => setTable(fn),
			),
	);

	return (
		<div className={frame}>
			<DataTable
				aria-label="Tasks on the server"
				columns={columns}
				rows={rows}
				selection="multi"
				selected={selected}
				onSelect={setSelected}
				sort={sort}
				onSort={(column, direction) =>
					ask(
						`sort ${column} ${direction}`,
						() => null,
						() => {
							setSort({ column, direction });
							setRows((prev) => sorted(prev, columns, column, direction));
						},
					)
				}
				onEdit={(e) =>
					ask(
						`edit ${e.key}.${e.column}`,
						() =>
							e.column === "title" && String(e.value).trim() === ""
								? "a title cannot be empty"
								: typeof e.value === "number" && e.value < 0
									? "points cannot be negative"
									: null,
						() => setRows((prev) => edited(prev, e, columns)),
					)
				}
				onAdd={(index) =>
					ask(
						`add at ${index}`,
						() => null,
						() => setRows((prev) => added(prev, index, columns)),
					)
				}
				onDelete={(keys) =>
					ask(
						`delete ${keys.length} row${keys.length === 1 ? "" : "s"}`,
						() =>
							live.current.every((r) => keys.includes(r.key))
								? "the table keeps at least one row"
								: null,
						() => {
							setRows((prev) => prev.filter((r) => !keys.includes(r.key)));
							setSelected((prev) => prev.filter((k) => !keys.includes(k)));
						},
					)
				}
				onMove={(key, index) =>
					ask(
						`move ${key} to ${index}`,
						() => null,
						() => {
							setSort(null);
							setRows((prev) => moved(prev, key, index));
						},
					)
				}
				{...ops}
			/>
			<Text size="xs" tone={status.tone} mono>
				{status.text}
			</Text>
		</div>
	);
}

// --- Column kinds ------------------------------------------------------------

const KINDS: DataTableColumn[] = [
	{ key: "name", label: "Text" },
	{ key: "count", label: "Number", kind: "number" },
	{ key: "on", label: "Bool", kind: "bool" },
	{ key: "level", label: "Select", kind: "select", options: ["low", "medium", "high"] },
	{ key: "meta", label: "Object", editable: false },
];

const KIND_ROWS: DataTableRow[] = [
	{ key: "a", cells: ["alpha", 1200, true, "high", { tags: ["x"] }] },
	{ key: "b", cells: ["beta", 3.5, false, "low", null] },
	{ key: "c", cells: ["", -42, true, "medium", [1, 2]] },
];

function Kinds() {
	const [table, setTable] = useState<Table>({ columns: KINDS, rows: KIND_ROWS });
	const [log, setLog] = useState("Column type and alignment switch from the column handle");
	const { onColumnKind, onColumnAlign } = columnOps(setTable, setLog);
	return (
		<div className={`${frame} space-y-8`}>
			<div className="space-y-2">
				<Text size="sm" tone="secondary">
					Editable: text and number open an editor, bool flips, select opens its list
				</Text>
				<DataTable
					aria-label="Kinds, editable"
					columns={table.columns}
					rows={table.rows}
					onEdit={(e) => setTable((t) => ({ ...t, rows: edited(t.rows, e, t.columns) }))}
					onColumnKind={onColumnKind}
					onColumnAlign={onColumnAlign}
				/>
				<Text size="xs" tone="muted" mono>
					{log}
				</Text>
			</div>
			<div className="space-y-2">
				<Text size="sm" tone="secondary">
					Read-only: the same values, nothing edits
				</Text>
				<DataTable
					aria-label="Kinds, read-only"
					columns={KINDS}
					rows={KIND_ROWS}
					density="compact"
					striped
				/>
			</div>
		</div>
	);
}

const meta: Meta = {
	title: "UI/DataTable",
};

export default meta;

export const Default: StoryObj = { render: () => <ReadOnly /> };

export const Playground: StoryObj<Args> = {
	args: {
		selection: "multi",
		editable: true,
		addable: true,
		deletable: true,
		movable: true,
		sortable: true,
		activatable: false,
		columnsEditable: true,
		density: "default",
		striped: false,
		variant: "default",
	},
	argTypes: {
		selection: { control: "inline-radio", options: ["none", "single", "multi"] },
		density: { control: "inline-radio", options: ["compact", "default", "comfortable"] },
		variant: { control: "inline-radio", options: ["default", "borderless"] },
	},
	render: (args) => <PlaygroundHost {...args} />,
};

export const ServerConfirm: StoryObj = {
	render: () => <ServerHost />,
};

export const ColumnKinds: StoryObj = { render: () => <Kinds /> };
