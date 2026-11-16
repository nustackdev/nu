// File primitive: a file you can open or save, drawn as one row. Its kind's
// glyph in a framed square, its name, a line with its size and type, and a
// download link at the end, like the media players' rows.
// Design refs:
//   typography.md    §Body (name base medium, meta xs muted)
//   palette.md       bg-hover / bg-press on the name link
//   space-radius.md  §radius md row; §Density 32px mark at md
//   motion.md        §3 row hover (bg + color, duration-fast ease-out)
//
// The name is a real <a href target="_blank"> to `src`, so the browser opens
// what it can show (a pdf, a text file) in a new tab, and middle click and
// copy link work for free. `download` is a separate url that saves the file
// (a blob's `?download=1` url, so the saved name is the server's). With no
// `src` the row is muted and inert, named `name` or "No file", so a file set
// later has a place to land.
//
// The glyph follows the mime's kind (image, video, audio, text, archive,
// sheet, code) and falls back to a plain file. A size that is not a
// non-negative number draws no size.

import {
	FileArchive,
	FileAudio,
	FileCode,
	File as FileIcon,
	FileImage,
	FileSpreadsheet,
	FileText,
	FileVideo,
	type LucideIcon,
} from "lucide-react";
import type * as React from "react";
import { formatBytes } from "../../lib/count";
import { cn } from "../../lib/utils";
import { Icon } from "./icon";
import { MediaDownloadButton } from "./media-controls";
import { TooltipProvider } from "./tooltip";

const ARCHIVES = ["zip", "x-tar", "gzip", "x-7z-compressed", "x-rar-compressed", "x-bzip2"];
const SHEETS = ["csv", "vnd.ms-excel", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"];
const CODE = ["json", "javascript", "x-python", "xml", "x-sh", "toml", "yaml", "x-yaml"];

/** The glyph for a mime type: its kind's file icon, a plain file when unknown. */
export function fileGlyph(mime: string): LucideIcon {
	const [kind = "", sub = ""] = mime.toLowerCase().split(";", 1)[0].trim().split("/");
	if (kind === "image") return FileImage;
	if (kind === "video") return FileVideo;
	if (kind === "audio") return FileAudio;
	if (SHEETS.includes(sub) || sub === "tab-separated-values") return FileSpreadsheet;
	if (ARCHIVES.includes(sub)) return FileArchive;
	if (CODE.includes(sub)) return FileCode;
	if (kind === "text" || sub === "pdf" || sub === "markdown") return FileText;
	return FileIcon;
}

/** The last path segment of `src`, decoded, without query or hash; "" when there is none. */
export function fileName(src: string): string {
	const path = src.split(/[?#]/, 1)[0] ?? "";
	const last = path.slice(path.lastIndexOf("/") + 1);
	try {
		return decodeURIComponent(last);
	} catch {
		return last;
	}
}

/** A short type label: the mime's subtype upper cased (PDF, PNG), "" without one. */
export function fileType(mime: string): string {
	const sub = mime.toLowerCase().split(";", 1)[0].trim().split("/")[1] ?? "";
	if (!sub) return "";
	const tail = sub.split(/[.+-]/).filter(Boolean).at(-1) ?? sub;
	return tail.length <= 5 ? tail.toUpperCase() : "";
}

export interface FileProps extends Omit<React.ComponentProps<"div">, "children"> {
	/** Where the file opens; none draws the row muted and inert. */
	src?: string;
	/** What the row reads; the last part of `src` when empty. */
	name?: string;
	/** Bytes, drawn in decimal units (48.2 KB). */
	size?: number | null;
	/** The file's mime type: picks the glyph and the type label. */
	mime?: string;
	/** A url that saves the file: a download link at the end of the row. */
	download?: string;
}

export function File({ src, name, size, mime = "", download, className, ...props }: FileProps) {
	const empty = !src;
	const title = name || (src ? fileName(src) || src : "No file");
	const bytes = typeof size === "number" && Number.isFinite(size) && size >= 0 ? size : null;
	const meta = [bytes == null ? "" : formatBytes(bytes), fileType(mime)]
		.filter(Boolean)
		.join(" · ");
	const body = (
		<>
			<Icon icon={fileGlyph(mime)} framed size="md" className="shrink-0" />
			<span className="flex min-w-0 flex-1 flex-col gap-0.5">
				<span data-slot="file-name" className="truncate text-base font-medium" title={title}>
					{title}
				</span>
				{meta ? (
					<span data-slot="file-meta" className="truncate text-xs text-text-muted tabular-nums">
						{meta}
					</span>
				) : null}
			</span>
		</>
	);
	return (
		<TooltipProvider>
			<div
				data-slot="file"
				data-empty={empty || undefined}
				className={cn("flex min-w-0 items-center gap-1", className)}
				{...props}
			>
				{empty ? (
					<span
						aria-disabled
						className="flex min-w-0 flex-1 items-center gap-3 rounded-md px-2 py-1.5 text-text-muted"
					>
						{body}
					</span>
				) : (
					<a
						data-slot="file-link"
						href={src}
						target="_blank"
						rel="noreferrer"
						className={cn(
							"flex min-w-0 flex-1 items-center gap-3 rounded-md px-2 py-1.5",
							"cursor-default text-text-primary no-underline focus-ring",
							"transition-colors duration-fast ease-out hover:bg-bg-hover active:bg-bg-press",
						)}
					>
						{body}
					</a>
				)}
				{download && !empty ? <MediaDownloadButton href={download} /> : null}
			</div>
		</TooltipProvider>
	);
}
