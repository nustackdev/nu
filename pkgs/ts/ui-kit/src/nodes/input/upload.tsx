// UploadFileRef and UploadFilesRef -- a person hands files to the program.
// Browser is source of truth.
//
// Both draw the kit FileInput (click to pick, drop, paste, keyboard).
// UploadFileRef shows its picked file in the zone's place, with Replace and
// remove; UploadFilesRef keeps the zone and lists a FileRow per file under it.
// The zone's hint is built from `accept` and `max_size`. The value is one dict per file (`{key, name, mime, size,
// modified, state, sent, error}`): a dict or null on UploadFileRef, a list on
// UploadFilesRef. The files themselves stay in the browser, in the node's
// handle map (./upload-handles.ts), along with every command the program can
// send about them (pull, slice, cancel, discard, remove_file).
//
// A pick moves no bytes and sends `{event: "change"}` (./control.ts), as a
// remove from a row does. UploadFileRef replaces its file on a new pick;
// UploadFilesRef appends, and a pick past `max_files` keeps what fits and
// says what it left out. A file over `max_size`, or one `accept` does not
// take (checked on drops and pastes too), is refused at pick with a message
// under the control and never becomes the value.
//
// No progress bar: the row's small mark says picked, sending, sent or
// failed, and the app draws anything more from `on_progress`. A program
// cannot set a file, so a write takes chrome only; `reset` clears.

import { OPS } from "@nustackdev/ui-core";
import { useEffect, useId, useState } from "react";
import { FieldError, Label } from "../../components/ui/field";
import { FileInput, FileRow, type FileState } from "../../components/ui/file-input";
import { formatBytes } from "../../lib/count";
import { type NodeEntry, type NodeProps, useProp, useStringProp } from "../../tree";
import { useCommit, useControl } from "./control";
import { addFiles, dropFiles, prune, removeFile, uploadHandlers } from "./upload-handles";

type Row = { key: string; name: string; size: number; state: FileState; error: string };

function rowsOf(raw: unknown): Row[] {
	const list = Array.isArray(raw) ? raw : raw && typeof raw === "object" ? [raw] : [];
	return list.filter(
		(r): r is Row => Boolean(r) && typeof (r as { key?: unknown }).key === "string",
	);
}

function limit(raw: unknown): number | null {
	return typeof raw === "number" && Number.isFinite(raw) && raw >= 0 ? raw : null;
}

function names(files: File[]): string {
	const shown = files.slice(0, 3).map((f) => f.name);
	const more = files.length - shown.length;
	return more > 0 ? `${shown.join(", ")} and ${more} more` : shown.join(", ");
}

function UploadView({ path, multiple }: NodeProps & { multiple: boolean }) {
	const raw = useProp<unknown>(path, "value", null);
	const rows = rowsOf(raw);
	const accept = useStringProp(path, "accept");
	const prompt = useStringProp(path, "prompt");
	const maxSize = limit(useProp<unknown>(path, "max_size", null));
	const maxFilesProp = limit(useProp<unknown>(path, "max_files", null));
	const maxFiles = multiple ? maxFilesProp : null;
	const c = useControl(path);
	const { pick } = useCommit(path);
	const [notice, setNotice] = useState("");
	const noticeId = useId();
	const key = path.join("\u0000");

	// A Form's reset moves the value without asking the node: the handles follow.
	// biome-ignore lint/correctness/useExhaustiveDependencies: path is compared by value.
	useEffect(() => prune(path), [key, raw]);

	const take = (files: File[], refused: File[]) => {
		const notes: string[] = [];
		if (refused.length) notes.push(`Not accepted here: ${names(refused)}`);
		let fit = files;
		if (maxSize !== null) {
			const big = fit.filter((f) => f.size > maxSize);
			fit = fit.filter((f) => f.size <= maxSize);
			if (big.length) notes.push(`Over the ${formatBytes(maxSize)} limit: ${names(big)}`);
		}
		if (maxFiles !== null) {
			const room = Math.max(0, maxFiles - rows.length);
			if (fit.length > room) {
				notes.push(`Up to ${maxFiles} files. Left out: ${names(fit.slice(room))}`);
				fit = fit.slice(0, room);
			}
		}
		setNotice(notes.join(". "));
		if (fit.length) pick(addFiles(path, fit, !multiple));
	};

	const closed = c.disabled || c.readOnly;
	const describedBy = [c.describedBy, notice ? noticeId : null].filter(Boolean).join(" ");
	const remove = (key: string) => {
		if (closed) return;
		setNotice("");
		pick(removeFile(path, key));
	};
	const first = multiple ? null : (rows[0] ?? null);

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<FileInput
				{...c.aria}
				aria-describedby={describedBy || undefined}
				accept={accept}
				multiple={multiple}
				prompt={prompt || undefined}
				maxSize={maxSize}
				file={first}
				onRemove={first ? () => remove(first.key) : undefined}
				size={c.size}
				disabled={c.disabled}
				readOnly={c.readOnly}
				invalid={c.invalid}
				autoFocus={c.autoFocus}
				onFiles={take}
			/>
			{multiple && rows.length > 0 && (
				<ul className="flex flex-col">
					{rows.map((r) => (
						<FileRow
							key={r.key}
							name={r.name}
							size={r.size}
							state={r.state}
							error={r.error}
							disabled={c.disabled}
							onRemove={c.readOnly ? undefined : () => remove(r.key)}
						/>
					))}
				</ul>
			)}
			{notice && <FieldError id={noticeId}>{notice}</FieldError>}
		</div>
	);
}

function UploadFileView({ path }: NodeProps) {
	return <UploadView path={path} multiple={false} />;
}

function UploadFilesView({ path }: NodeProps) {
	return <UploadView path={path} multiple />;
}

/** The value as read: the empty one when the node has none yet. */
function readValue(empty: () => unknown) {
	return (props: Record<string, unknown>) => props.value ?? empty();
}

/**
 * The registry entry of a node whose value is files in the handle map: the
 * upload nodes, and the capture nodes with their own view.
 */
export function uploadEntry(component: NodeEntry["component"], empty: () => unknown): NodeEntry {
	const read = readValue(empty);
	return {
		component,
		fill: true,
		input: { empty, read },
		handlers: {
			...uploadHandlers,
			read: (ctx) => ctx.send(OPS.read, read(ctx.node.props), ctx.frame.id),
		},
		dispose: ({ path }) => dropFiles(path),
	};
}

export const UploadFileRef: NodeEntry = uploadEntry(UploadFileView, () => null);

export const UploadFilesRef: NodeEntry = uploadEntry(UploadFilesView, () => []);
