import { cva, type VariantProps } from "class-variance-authority";
import { Check, File as FileIcon, TriangleAlert, Upload, X } from "lucide-react";
import * as React from "react";
import { formatBytes } from "../../lib/count";
import { useTouch } from "../../lib/touch";
import { cn, ringVariants } from "../../lib/utils";
import { Button } from "./button";
import { IconButton } from "./icon-button";

// FileInput: where a person hands files to the page, and FileRow: one file
// once handed over.
//
// The zone is a real `<button>`: Tab reaches it, Enter or Space opens the
// system picker, and a `<label for>` names it. A drop and a paste (with the
// zone focused) hand files over the same way. A hidden `<input type=file>`
// does the picking; it is reset after each pick so the same file can be
// picked again. `accept` filters the picker, and drops and pastes are
// checked against it here too, since the browser checks only the picker:
// `onFiles` hears what matched and, apart, what did not. Under the prompt a
// quieter hint says what the zone takes ("CSV, up to 20 MB"), built from
// `accept` and `maxSize` unless `hint` says otherwise.
//
// One file (`multiple` off, `file` set): the file's row takes the zone's
// place, framed like an input of the same size, with Replace and remove. A
// drop or a paste on it replaces the file. The zone comes back when `file`
// goes back to null. Several files: the zone stays and the caller lists the
// rows under it.
//
// While any FileInput is mounted, a file dropped next to a zone is cancelled
// at the page, so the browser never opens it in the tab (that would end the
// session and every file handle with it). A disabled or read only zone
// cancels its drops too.
//
// Props the button takes (`id`, `aria-*`, handlers) land on the control: the
// zone, or Replace while a file shows. The zone's own handlers run after the
// caller's; a caller's `onClick` that calls `preventDefault` keeps the picker
// shut.
//
// The row shows a file's name and size and a small mark for its state. No
// progress bar: how a transfer is drawn is the app's call. A file that can no
// longer be read (changed on disk after the pick) is struck through and asks
// to be picked again.
//
// In touch mode (../../lib/touch.ts) nothing is dropped on a phone and
// nothing is clicked, so the default prompt says tap. The zone is already
// taller than a thumb; the frame's buttons carry their own tap areas.

// Two control rows tall at each size (24, 32, 40), text as the Input's.
const fileInputVariants = cva(
	[
		"flex w-full flex-col items-center justify-center gap-0.5 rounded-md text-center",
		"border border-dashed cursor-default select-none",
		"transition-[border-color,background-color,color] duration-fast ease-out",
		"focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring",
		ringVariants.offset,
		// The children never take the pointer, so a drag over the icon or the
		// text never reads as leaving the zone.
		"[&>*]:pointer-events-none [&_svg]:shrink-0",
	].join(" "),
	{
		variants: {
			size: {
				sm: "min-h-12 px-2 py-2 text-sm [&_svg]:size-3.5",
				md: "min-h-16 px-3 py-3 text-lg [&_svg]:size-4",
				lg: "min-h-20 px-4 py-4 text-lg [&_svg]:size-4.5",
			},
			tone: {
				rest: "border-border-default bg-bg-surface text-text-secondary hover:border-border-strong hover:bg-bg-hover hover:text-text-primary",
				// A drop target is marked with an Afterglow line, never a fill.
				over: "border-solid border-accent bg-bg-hover text-text-primary",
				invalid:
					"border-status-danger bg-bg-surface text-text-secondary hover:bg-bg-hover hover:text-text-primary focus-visible:ring-status-danger",
				readonly: "border-border-default bg-bg-surface text-text-muted",
				disabled:
					"cursor-not-allowed border-border-default bg-bg-sunken text-text-secondary opacity-50",
			},
		},
		defaultVariants: { size: "md", tone: "rest" },
	},
);

// The picked file in the zone's place: an input's frame at the same size.
const fileFrameVariants = cva(
	[
		"flex w-full items-center rounded-md border bg-bg-surface",
		"transition-[border-color,background-color] duration-fast ease-out",
	].join(" "),
	{
		variants: {
			size: {
				sm: "min-h-6 gap-1.5 py-px pl-2 pr-0.5 text-sm",
				md: "min-h-8 gap-2 py-0.5 pl-2.5 pr-1 text-lg",
				lg: "min-h-10 gap-2 py-0.5 pl-3 pr-1 text-lg",
			},
			tone: {
				rest: "border-border-default",
				over: "border-accent bg-bg-hover",
				invalid: "border-status-danger",
				readonly: "border-border-default",
				disabled: "border-border-default bg-bg-sunken opacity-50",
			},
		},
		defaultVariants: { size: "md", tone: "rest" },
	},
);

type Size = "sm" | "md" | "lg";
type Tone = "rest" | "over" | "invalid" | "readonly" | "disabled";

const FRAME_BUTTON: Record<Size, "xs" | "sm" | "md"> = { sm: "xs", md: "sm", lg: "md" };

/** Whether `file` matches an `accept` list (`.csv`, `image/*`, `text/plain`). */
export function accepts(file: { name: string; type: string }, accept: string): boolean {
	const rules = acceptRules(accept);
	if (rules.length === 0) return true;
	const name = file.name.toLowerCase();
	const type = file.type.toLowerCase();
	return rules.some((rule) => {
		if (rule.startsWith(".")) return name.endsWith(rule);
		if (rule.endsWith("/*")) return type.startsWith(rule.slice(0, -1));
		return type === rule;
	});
}

function acceptRules(accept: string): string[] {
	return accept
		.split(",")
		.map((r) => r.trim().toLowerCase())
		.filter(Boolean);
}

const KINDS: Record<string, string> = {
	"image/*": "Images",
	"video/*": "Videos",
	"audio/*": "Audio",
	"text/*": "Text files",
	"text/plain": "Text files",
};

/** A rule as people say it: `.csv` and `text/csv` are CSV, `image/*` is Images. */
function kindOf(rule: string): string {
	if (KINDS[rule]) return KINDS[rule];
	if (rule.startsWith(".")) return rule.slice(1).toUpperCase();
	const sub = rule.split("/")[1] ?? rule;
	return (sub.split(/[.+]/).at(-1) ?? sub).replace(/^x-/, "").toUpperCase();
}

/** What a zone takes, in a few words: "CSV, up to 20 MB", "Images", "Any file". */
export function fileHint(accept: string, maxSize?: number | null): string {
	const kinds = [...new Set(acceptRules(accept).map(kindOf))];
	const what =
		kinds.length === 0
			? "Any file"
			: kinds.length === 1
				? kinds[0]
				: `${kinds.slice(0, -1).join(", ")} or ${kinds.at(-1)}`;
	return maxSize != null && maxSize >= 0 ? `${what}, up to ${formatBytes(maxSize)}` : what;
}

function hasFiles(e: { dataTransfer: DataTransfer | null }): boolean {
	return Array.from(e.dataTransfer?.types ?? []).includes("Files");
}

// --- page guard: a file dropped beside a zone never opens in the tab ---------

let guarded = 0;

function cancelStray(e: DragEvent) {
	if (e.defaultPrevented || !hasFiles(e)) return;
	// A native file input takes drops on its own; leave it be.
	const t = e.target;
	if (t instanceof HTMLInputElement && t.type === "file") return;
	e.preventDefault();
	if (e.dataTransfer) e.dataTransfer.dropEffect = "none";
}

/** Installed with the first mounted FileInput, removed with the last. */
function usePageGuard() {
	React.useEffect(() => {
		guarded += 1;
		if (guarded === 1) {
			window.addEventListener("dragover", cancelStray);
			window.addEventListener("drop", cancelStray);
		}
		return () => {
			guarded -= 1;
			if (guarded === 0) {
				window.removeEventListener("dragover", cancelStray);
				window.removeEventListener("drop", cancelStray);
			}
		};
	}, []);
}

/** The one file a single FileInput shows in the zone's place. */
export type FileInputFile = Pick<FileRowProps, "name" | "size" | "state" | "error">;

export interface FileInputProps
	extends Omit<React.ComponentProps<"button">, "children">,
		Omit<VariantProps<typeof fileInputVariants>, "tone"> {
	/** Files the zone takes, as `<input accept>` spells it. Empty takes any. */
	accept?: string;
	/** Take several files at once. */
	multiple?: boolean;
	/** The zone's text. */
	prompt?: React.ReactNode;
	/** The quieter line under the prompt. Built from `accept` and `maxSize` when left out; "" draws none. */
	hint?: React.ReactNode;
	/** The largest file the zone takes, in bytes, for the hint. The caller enforces it. */
	maxSize?: number | null;
	/** One file only: the picked file, drawn in the zone's place with Replace and remove. */
	file?: FileInputFile | null;
	/** One file only: draws the remove button beside Replace. */
	onRemove?: () => void;
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

export function FileInput({
	accept = "",
	multiple = false,
	prompt,
	hint,
	maxSize,
	file,
	onRemove,
	size,
	disabled = false,
	readOnly = false,
	invalid = false,
	onFiles,
	className,
	onClick,
	onDragEnter,
	onDragOver,
	onDragLeave,
	onDrop,
	onPaste,
	...props
}: FileInputProps) {
	usePageGuard();
	const touch = useTouch();
	const input = React.useRef<HTMLInputElement>(null);
	const control = React.useRef<HTMLButtonElement>(null);
	const depth = React.useRef(0);
	const refocus = React.useRef(false);
	const [over, setOver] = React.useState(false);
	const hintId = React.useId();
	const closed = disabled || readOnly;
	const s: Size = size ?? "md";
	const shown = !multiple && file ? file : null;
	const tone: Tone = disabled
		? "disabled"
		: readOnly
			? "readonly"
			: over
				? "over"
				: invalid
					? "invalid"
					: "rest";

	// The control swaps (zone for Replace, or back) after a pick or a remove:
	// focus follows when it was ours.
	const ours = () => {
		refocus.current = Boolean(control.current && control.current === document.activeElement);
	};
	// biome-ignore lint/correctness/useExhaustiveDependencies: runs when the layout swaps.
	React.useLayoutEffect(() => {
		if (!refocus.current) return;
		refocus.current = false;
		control.current?.focus();
	}, [shown === null]);

	const take = (list: FileList | File[] | null | undefined) => {
		if (closed || !list) return;
		const all = Array.from(list);
		if (all.length === 0) return;
		const handed = multiple ? all : all.slice(0, 1);
		const fit = handed.filter((f) => accepts(f, accept));
		const refused = handed.filter((f) => !accepts(f, accept));
		onFiles(fit, refused);
	};

	const pick = () => {
		if (!closed) input.current?.click();
	};

	// Drag and paste, the same on the zone and on the picked file's frame. An
	// enter / leave count keeps the mark steady over the frame's buttons.
	const drag = {
		onDragEnter: (e: React.DragEvent<HTMLElement>) => {
			if (!hasFiles(e)) return;
			e.preventDefault();
			if (closed) return;
			depth.current += 1;
			setOver(true);
		},
		onDragOver: (e: React.DragEvent<HTMLElement>) => {
			if (!hasFiles(e)) return;
			e.preventDefault();
			e.dataTransfer.dropEffect = closed ? "none" : "copy";
		},
		onDragLeave: () => {
			depth.current = Math.max(0, depth.current - 1);
			if (depth.current === 0) setOver(false);
		},
		onDrop: (e: React.DragEvent<HTMLElement>) => {
			e.preventDefault();
			depth.current = 0;
			setOver(false);
			take(e.dataTransfer?.files);
		},
		onPaste: (e: React.ClipboardEvent<HTMLElement>) => {
			const files = e.clipboardData?.files;
			if (!files || files.length === 0) return;
			e.preventDefault();
			ours();
			take(files);
		},
	};

	const picker = (
		<input
			ref={input}
			type="file"
			data-slot="file-input-input"
			className="hidden"
			tabIndex={-1}
			aria-hidden
			accept={accept || undefined}
			multiple={multiple}
			disabled={closed}
			onChange={(e) => {
				ours();
				take(e.currentTarget.files);
				e.currentTarget.value = "";
			}}
		/>
	);

	if (shown) {
		const button = FRAME_BUTTON[s];
		return (
			<>
				<div
					data-slot="file-input"
					data-picked=""
					data-over={over || undefined}
					// Read only draws no buttons: the id stays findable on the frame.
					id={readOnly ? props.id : undefined}
					className={cn(fileFrameVariants({ size: s, tone }), className)}
					{...drag}
				>
					<FileRowBody
						name={shown.name}
						size={shown.size}
						state={shown.state}
						error={shown.error}
						compact={s === "sm"}
						framed
					/>
					{readOnly ? null : (
						<>
							<Button
								variant="ghost"
								size={button}
								ring="inset"
								disabled={disabled}
								aria-invalid={invalid || undefined}
								{...props}
								ref={control}
								aria-label={`Replace ${shown.name}`}
								className={cn("shrink-0", disabled && "disabled:opacity-100")}
								onClick={(e) => {
									onClick?.(e);
									if (!e.defaultPrevented) pick();
								}}
								onDragEnter={onDragEnter}
								onDragOver={onDragOver}
								onDragLeave={onDragLeave}
								onDrop={onDrop}
								onPaste={onPaste}
							>
								Replace
							</Button>
							{onRemove ? (
								<IconButton
									variant="ghost"
									size={button}
									ring="inset"
									aria-label={`Remove ${shown.name}`}
									disabled={disabled}
									className={cn(disabled && "disabled:opacity-100")}
									onClick={() => {
										refocus.current = true;
										onRemove();
									}}
								>
									<X aria-hidden />
								</IconButton>
							) : null}
						</>
					)}
				</div>
				{picker}
			</>
		);
	}

	const text =
		prompt ||
		(readOnly
			? "Read only"
			: touch
				? multiple
					? "Tap to choose files"
					: "Tap to choose a file"
				: multiple
					? "Drop files or click to choose"
					: "Drop a file or click to choose");
	const line =
		readOnly && hint === undefined ? "" : hint === undefined ? fileHint(accept, maxSize) : hint;
	const hasHint = line !== "" && line !== null && line !== false;
	const describedBy =
		[hasHint ? hintId : null, props["aria-describedby"]].filter(Boolean).join(" ") || undefined;

	return (
		<>
			<button
				type="button"
				data-slot="file-input"
				data-over={over || undefined}
				disabled={disabled}
				aria-disabled={readOnly || undefined}
				aria-invalid={invalid || undefined}
				{...props}
				ref={control}
				aria-describedby={describedBy}
				className={cn(fileInputVariants({ size: s, tone }), className)}
				onClick={(e) => {
					onClick?.(e);
					if (!e.defaultPrevented) pick();
				}}
				onDragEnter={(e) => {
					onDragEnter?.(e);
					drag.onDragEnter(e);
				}}
				onDragOver={(e) => {
					onDragOver?.(e);
					drag.onDragOver(e);
				}}
				onDragLeave={(e) => {
					onDragLeave?.(e);
					drag.onDragLeave();
				}}
				onDrop={(e) => {
					onDrop?.(e);
					drag.onDrop(e);
				}}
				onPaste={(e) => {
					onPaste?.(e);
					drag.onPaste(e);
				}}
			>
				<span className="flex items-center gap-2">
					{readOnly ? null : <Upload aria-hidden />}
					<span>{text}</span>
				</span>
				{hasHint ? (
					// Out of the name, into the description: read once, after the label.
					<span
						id={hintId}
						aria-hidden
						className={cn("text-text-muted", s === "lg" ? "text-sm" : "text-xs")}
					>
						{line}
					</span>
				) : null}
			</button>
			{picker}
		</>
	);
}

/** Where a file stands: handed over, on its way, at the server, or failed. */
export type FileState = "picked" | "pulling" | "landed" | "failed";

// Color is never the only signal: each mark has its own glyph and a word.
// Sending is live, so it is Starlight; Afterglow is kept for acting.
const MARKS: Record<FileState, { icon: React.ReactNode; label: string; className: string }> = {
	picked: { icon: <FileIcon aria-hidden />, label: "Picked", className: "text-text-muted" },
	pulling: { icon: <Upload aria-hidden />, label: "Sending", className: "text-accent-2" },
	landed: { icon: <Check aria-hidden />, label: "Sent", className: "text-status-ok" },
	failed: { icon: <TriangleAlert aria-hidden />, label: "Failed", className: "text-status-danger" },
};

/** The mark, the name and the size, and the line a file changed on disk adds. */
function FileRowBody({
	name,
	size,
	state = "picked",
	error = "",
	compact = true,
	framed = false,
}: FileInputFile & { compact?: boolean; framed?: boolean }) {
	const mark = MARKS[state] ?? MARKS.picked;
	const gone = error === "unreadable";
	return (
		<span
			// In a list the `<li>` is the row; in the frame this is.
			data-slot={framed ? "file-row" : undefined}
			data-state={framed ? state : undefined}
			className="flex min-w-0 flex-1 items-center gap-2"
		>
			<span
				className={cn(
					"flex shrink-0 [&_svg]:shrink-0",
					compact ? "[&_svg]:size-3.5" : "[&_svg]:size-4",
					mark.className,
				)}
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
					<span
						className={cn("shrink-0 text-text-muted tabular-nums", compact ? "text-xs" : "text-sm")}
					>
						{formatBytes(size)}
					</span>
				</span>
				{gone ? (
					<span className="text-xs text-status-danger">
						Changed on disk since it was picked. Pick it again.
					</span>
				) : null}
			</span>
		</span>
	);
}

export interface FileRowProps extends React.ComponentProps<"li"> {
	name: string;
	/** The file's size in bytes. */
	size: number;
	state?: FileState;
	/** The last failure's code, "" when none. `unreadable` strikes the row. */
	error?: string;
	/** Draws a remove button that calls this. */
	onRemove?: () => void;
	disabled?: boolean;
}

/** One file in a list: name, size, a state mark, and a remove button when asked. */
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
	return (
		// 28 high, a dense list row: a 20px remove button with 4px around it.
		<li
			data-slot="file-row"
			data-state={state}
			className={cn(
				"flex min-h-7 items-center gap-2 rounded-md py-1 pl-2 pr-1 text-sm",
				disabled && "opacity-50",
				className,
			)}
			{...props}
		>
			<FileRowBody name={name} size={size} state={state} error={error} />
			{onRemove ? (
				<IconButton
					variant="ghost"
					size="xs"
					ring="inset"
					aria-label={`Remove ${name}`}
					disabled={disabled}
					className={cn(disabled && "disabled:opacity-100")}
					onClick={onRemove}
				>
					<X aria-hidden />
				</IconButton>
			) : null}
		</li>
	);
}

export { fileFrameVariants, fileInputVariants };
