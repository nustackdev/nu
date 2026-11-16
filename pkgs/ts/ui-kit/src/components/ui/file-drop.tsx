import { cva, type VariantProps } from "class-variance-authority";
import { Check, File as FileIcon, TriangleAlert, Upload, X } from "lucide-react";
import * as React from "react";
import { cn } from "../../lib/utils";
import { IconButton } from "./icon-button";

// FileDrop: where a person hands files to the page, and FileRow: one file
// once handed over.
//
// The zone is a real `<button>`: Tab reaches it, Enter or Space opens the
// system picker, and a `<label for>` names it. A drop and a paste (with the
// zone focused) hand files over the same way. A hidden `<input type=file>`
// does the picking; it is reset after each pick so the same file can be
// picked again. `accept` filters the picker, and drops and pastes are
// checked against it here too, since the browser checks only the picker:
// `onFiles` hears what matched and, apart, what did not.
//
// The row shows a file's name and size and a small mark for its state. No
// progress bar: how a transfer is drawn is the app's call. A file that can no
// longer be read (changed on disk after the pick) is struck through and asks
// to be picked again.

const fileDropVariants = cva(
	[
		"flex w-full items-center justify-center gap-2 rounded-md text-center",
		"border border-dashed cursor-default select-none",
		"transition-[border-color,background-color] duration-fast ease-out",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
		"focus-visible:ring-offset-2 focus-visible:ring-offset-bg-canvas",
		"[&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			size: {
				sm: "min-h-12 px-2 py-2 text-sm [&_svg]:size-3.5",
				md: "min-h-16 px-3 py-3 text-base [&_svg]:size-4",
				lg: "min-h-24 px-4 py-4 text-lg [&_svg]:size-5",
			},
			tone: {
				rest: "border-border-default bg-bg-surface text-text-secondary hover:border-border-strong hover:bg-bg-hover",
				over: "border-accent-line bg-accent-soft text-text-primary",
				invalid:
					"border-status-danger bg-bg-surface text-text-secondary focus-visible:ring-status-danger",
			},
			disabled: {
				true: "cursor-not-allowed opacity-50 bg-bg-sunken hover:bg-bg-sunken hover:border-border-default",
				false: "",
			},
		},
		defaultVariants: { size: "md", tone: "rest", disabled: false },
	},
);

/** Whether `file` matches an `accept` list (`.csv`, `image/*`, `text/plain`). */
export function accepts(file: { name: string; type: string }, accept: string): boolean {
	const rules = accept
		.split(",")
		.map((r) => r.trim().toLowerCase())
		.filter(Boolean);
	if (rules.length === 0) return true;
	const name = file.name.toLowerCase();
	const type = file.type.toLowerCase();
	return rules.some((rule) => {
		if (rule.startsWith(".")) return name.endsWith(rule);
		if (rule.endsWith("/*")) return type.startsWith(rule.slice(0, -1));
		return type === rule;
	});
}

const UNITS = ["B", "KB", "MB", "GB", "TB"];

/** A byte count for people: 812 B, 4.2 KB, 1.3 GB. */
export function formatBytes(n: number): string {
	let value = n;
	let unit = 0;
	while (value >= 1024 && unit < UNITS.length - 1) {
		value /= 1024;
		unit += 1;
	}
	const digits = unit === 0 || value >= 100 ? 0 : 1;
	return `${value.toFixed(digits)} ${UNITS[unit]}`;
}

export interface FileDropProps
	extends Omit<React.ComponentProps<"button">, "onDrop" | "onPaste" | "children">,
		Omit<VariantProps<typeof fileDropVariants>, "tone" | "disabled"> {
	/** Files the zone takes, as `<input accept>` spells it. Empty takes any. */
	accept?: string;
	/** Take several files at once. */
	multiple?: boolean;
	/** The zone's text. */
	prompt?: React.ReactNode;
	disabled?: boolean;
	/** Draws and takes focus (`aria-disabled`), refuses files. */
	readOnly?: boolean;
	invalid?: boolean;
	/**
	 * Files handed over, in the order given: those that match `accept`, and
	 * those that do not. Called once per pick, drop or paste.
	 */
	onFiles: (files: File[], refused: File[]) => void;
}

export function FileDrop({
	accept = "",
	multiple = false,
	prompt,
	size,
	disabled = false,
	readOnly = false,
	invalid = false,
	onFiles,
	className,
	...props
}: FileDropProps) {
	const input = React.useRef<HTMLInputElement>(null);
	const [over, setOver] = React.useState(false);
	const closed = disabled || readOnly;

	const take = (list: FileList | File[] | null | undefined) => {
		if (closed || !list) return;
		const all = Array.from(list);
		if (all.length === 0) return;
		const handed = multiple ? all : all.slice(0, 1);
		const fit = handed.filter((f) => accepts(f, accept));
		const refused = handed.filter((f) => !accepts(f, accept));
		onFiles(fit, refused);
	};

	const text =
		prompt || (multiple ? "Drop files or click to choose" : "Drop a file or click to choose");

	return (
		<>
			<button
				type="button"
				data-slot="file-drop"
				data-over={over || undefined}
				disabled={disabled}
				aria-disabled={readOnly || undefined}
				aria-invalid={invalid || undefined}
				className={cn(
					fileDropVariants({ size, tone: over ? "over" : invalid ? "invalid" : "rest", disabled }),
					className,
				)}
				onClick={() => {
					if (!closed) input.current?.click();
				}}
				onDragOver={(e) => {
					if (closed) return;
					e.preventDefault();
					e.dataTransfer.dropEffect = "copy";
					setOver(true);
				}}
				onDragLeave={() => setOver(false)}
				onDrop={(e) => {
					e.preventDefault();
					setOver(false);
					take(e.dataTransfer?.files);
				}}
				onPaste={(e) => {
					const files = e.clipboardData?.files;
					if (!files || files.length === 0) return;
					e.preventDefault();
					take(files);
				}}
				{...props}
			>
				<Upload aria-hidden />
				<span>{text}</span>
			</button>
			<input
				ref={input}
				type="file"
				data-slot="file-drop-input"
				className="hidden"
				tabIndex={-1}
				aria-hidden
				accept={accept || undefined}
				multiple={multiple}
				disabled={closed}
				onChange={(e) => {
					take(e.currentTarget.files);
					e.currentTarget.value = "";
				}}
			/>
		</>
	);
}

/** Where a file stands: handed over, on its way, at the server, or failed. */
export type FileState = "picked" | "pulling" | "landed" | "failed";

const MARKS: Record<FileState, { icon: React.ReactNode; label: string; className: string }> = {
	picked: { icon: <FileIcon aria-hidden />, label: "Picked", className: "text-text-muted" },
	pulling: { icon: <Upload aria-hidden />, label: "Sending", className: "text-accent-text" },
	landed: { icon: <Check aria-hidden />, label: "Sent", className: "text-status-ok" },
	failed: { icon: <TriangleAlert aria-hidden />, label: "Failed", className: "text-status-danger" },
};

export interface FileRowProps extends React.ComponentProps<"li"> {
	name: string;
	size: number;
	state?: FileState;
	/** The last failure's code, "" when none. `unreadable` strikes the row. */
	error?: string;
	/** Draws a remove button that calls this. */
	onRemove?: () => void;
	disabled?: boolean;
}

/** One file: name, size, a state mark, and a remove button when asked. */
export function FileRow({
	name,
	size,
	state = "picked",
	error = "",
	onRemove,
	disabled = false,
	className,
	...props
}: FileRowProps) {
	const mark = MARKS[state] ?? MARKS.picked;
	const gone = error === "unreadable";
	return (
		<li
			data-slot="file-row"
			data-state={state}
			className={cn("flex min-h-7 items-center gap-2 rounded-md px-1.5 text-sm", className)}
			{...props}
		>
			<span
				className={cn("flex [&_svg]:size-3.5 [&_svg]:shrink-0", mark.className)}
				title={mark.label}
			>
				{mark.icon}
				<span className="sr-only">{mark.label}</span>
			</span>
			<span className="flex min-w-0 flex-1 flex-col">
				<span className="flex min-w-0 items-baseline gap-2">
					<span
						className={cn("truncate text-text-primary", gone && "line-through text-text-secondary")}
						title={name}
					>
						{name}
					</span>
					<span className="shrink-0 text-xs text-text-muted tabular-nums">{formatBytes(size)}</span>
				</span>
				{gone ? (
					<span className="text-xs text-status-danger">
						Changed on disk since it was picked. Pick it again.
					</span>
				) : null}
			</span>
			{onRemove ? (
				<IconButton
					variant="ghost"
					size="xs"
					ring="inset"
					aria-label={`Remove ${name}`}
					disabled={disabled}
					onClick={onRemove}
				>
					<X aria-hidden />
				</IconButton>
			) : null}
		</li>
	);
}

export { fileDropVariants };
