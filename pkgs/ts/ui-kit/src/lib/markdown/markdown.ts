// Markdown in, markdown out.
//
// The Ref's value is a markdown string and stays one. The wire, the server
// and the Nu program never learn that a document engine exists in the
// browser. That is the point: the editor is a *view* over markdown, not a new
// format with a markdown export.
//
// Which is why this is hand-written rather than borrowed. A markdown library
// is a document model in disguise, and the one thing that has to be true here
// is that the parser and the serializer are exact inverses of each other over
// the dialect the editor can actually produce - which is exactly the dialect
// the input rules offer, and nothing else. A general parser accepting far more
// than we emit is how round-trips start churning. `matchDelim` is shared by
// both directions, so a construct can never be emitted unescaped that the
// parser would then read back differently.
//
// The one normalization that is not identity: a paragraph hard-wrapped across
// source lines comes back as a single line. Reflowing is what a WYSIWYG
// *means* - the alternative is showing the author their source wrapping as if
// it were content. Nothing commits unless the document actually changed, so
// untouched values never churn.
//
// ## Tables
//
// GFM pipe tables: a header row, a delimiter row that sets each column's
// alignment, then body rows, up to a blank line or the next block. Cells hold
// inline content only, the way GitHub's do. One form is written back, whatever
// was read:
//
//     | Name | Qty | Note |
//     | :--- | ---: | :---: |
//     | a | 1 |  |
//
// Leading and trailing pipes, one space either side of a cell, and no padding
// to column width, so editing one cell rewrites one line instead of every row
// in the table and the stored diff is the edit. A hand-written table settles
// into this form in one lap: missing outer pipes, ragged widths, longer
// dashes, and rows shorter or longer than the header (padded with empty
// cells, or cut, as GFM does). A cell keeps no edge whitespace, the same as a
// table cell anywhere.
//
// A pipe inside a cell is `\|`, inline code included: the row is split on
// pipes before a cell is read as inline markdown, so that one escape is
// resolved first and everything else reads as it would in a paragraph.
//
// The pair of lines is the whole signal: a header line holding a pipe, then a
// delimiter line of `---`, `:---`, `:---:` or `---:` cells with the same
// count. Nothing else the serializer writes can form that pair. A paragraph is
// always one line with a blank line after it, and the only lines written
// straight under one are a nested list's, which open with a list marker, and
// a line that opens a block is never a delimiter row. So prose holding pipes
// needs no table escaping, and `| a |` alone stays a paragraph.

import type { Mark, Node as PMNode } from "prosemirror-model";
import type { ProseSchema } from "./schema";
import { proseSchema } from "./schema";

/* ============================== source lines ============================= */

/** A source line plus the absolute offset of its first character. */
type Line = { text: string; at: number };

function toLines(src: string): Line[] {
	const out: Line[] = [];
	let at = 0;
	for (const text of src.split("\n")) {
		out.push({ text, at });
		at += text.length + 1;
	}
	return out;
}

/**
 * A run of text with a per-character map back into the source. Paragraphs are
 * built by joining wrapped lines, so the mapping is not affine and has to be
 * carried explicitly. It is what lets a host put the caret at an exact source
 * offset rather than at one end of the document.
 */
type Src = { text: string; map: number[] };

function joinLines(lines: Line[]): Src {
	const text: string[] = [];
	const map: number[] = [];
	lines.forEach((line, i) => {
		if (i > 0) {
			text.push(" ");
			map.push(line.at);
		}
		for (let k = 0; k < line.text.length; k++) {
			text.push(line.text[k]);
			map.push(line.at + k);
		}
	});
	return { text: text.join(""), map };
}

function sliceSrc(s: Src, from: number, to: number): Src {
	return { text: s.text.slice(from, to), map: s.map.slice(from, to) };
}

/* ============================== inline grammar =========================== */

const ESCAPABLE = /[\\`*_[\]()#+\-.!>]/;

type Delim =
	| { kind: "image"; inner: [number, number]; next: number; href: string }
	| { kind: "code"; inner: [number, number]; next: number }
	| { kind: "strong"; inner: [number, number]; next: number }
	| { kind: "em"; inner: [number, number]; next: number }
	| { kind: "link"; inner: [number, number]; next: number; href: string };

/** Index of the next unescaped occurrence of `token` at or after `from`. */
function findUnescaped(text: string, token: string, from: number): number {
	for (let i = from; i <= text.length - token.length; i++) {
		if (text[i] === "\\") {
			i += 1;
			continue;
		}
		if (text.startsWith(token, i)) return i;
	}
	return -1;
}

/**
 * The whole inline grammar, in one place, used by both directions. The
 * serializer escapes exactly what this matches, so nothing it emits can be
 * re-read as markup that was not there. Schema-independent, so it lives
 * outside the factory.
 */
export function matchDelim(text: string, i: number): Delim | null {
	const c = text[i];

	if (c === "!" && text[i + 1] === "[") {
		const link = matchDelim(text, i + 1);
		if (link?.kind !== "link") return null;
		return { kind: "image", inner: link.inner, next: link.next, href: link.href };
	}

	if (c === "`") {
		const j = findUnescaped(text, "`", i + 1);
		if (j > i + 1) return { kind: "code", inner: [i + 1, j], next: j + 1 };
		return null;
	}

	if (c === "*" || c === "_") {
		const double = c + c;
		if (text.startsWith(double, i)) {
			const j = findUnescaped(text, double, i + 2);
			if (j > i + 2) return { kind: "strong", inner: [i + 2, j], next: j + 2 };
			return null;
		}
		const j = findUnescaped(text, c, i + 1);
		if (j > i + 1) return { kind: "em", inner: [i + 1, j], next: j + 1 };
		return null;
	}

	if (c === "[") {
		const close = findUnescaped(text, "]", i + 1);
		if (close < 0 || text[close + 1] !== "(") return null;
		const end = findUnescaped(text, ")", close + 2);
		if (end < 0) return null;
		return {
			kind: "link",
			inner: [i + 1, close],
			next: end + 1,
			href: text.slice(close + 2, end),
		};
	}

	return null;
}

/* ============================== block grammar ============================ */

const RULE = /^(---|\*\*\*|___)\s*$/;
const HEADING = /^(#{1,6})[ \t]+(.*)$/;
/** A code fence: three or more backticks or tildes, then an optional language. */
const FENCE = /^(`{3,}|~{3,})[ \t]*([^`\s]*)[ \t]*$/;
const QUOTE = /^>[ \t]?/;
const BULLET = /^([ \t]*)([-*+])([ \t]+)/;
const ORDERED = /^([ \t]*)(\d+)([.)])([ \t]+)/;
/** A checklist item: a bullet, then `[ ]` or `[x]`. Tried before BULLET. */
const TASK = /^([ \t]*)([-*+])([ \t]+)\[([ xX])\](?:[ \t]+|$)/;
/** One delimiter-row cell, trimmed: dashes, a colon on the aligned side(s). */
const DELIM_CELL = /^(:?)-+(:?)$/;

/**
 * A language as a fence can carry it: what FENCE reads back, so no whitespace
 * and no backtick. The serializer writes only this, so a language attribute
 * set from anywhere (a picker, a paste, a host) can never turn its fence line
 * into text and shift every fence after it.
 */
export function fenceInfo(language: string): string {
	return language.replace(/[\s`]+/g, "");
}

/** A column's alignment, as the delimiter row spells it. */
export type Align = "left" | "center" | "right" | null;

/** Index of each pipe in `text` that is a cell boundary, i.e. not written `\|`. */
function pipes(text: string): number[] {
	const out: number[] = [];
	for (let i = 0; i < text.length; i++) {
		if (text[i] === "|" && text[i - 1] !== "\\") out.push(i);
	}
	return out;
}

/**
 * A table row's cells as [from, to) offsets into `text`, untrimmed. The outer
 * pipes are optional; every other unescaped pipe is a boundary.
 */
function rowCells(text: string): [number, number][] {
	const bounds = pipes(text);
	let from = leadingWs(text);
	let to = text.trimEnd().length;
	if (bounds[0] === from) {
		bounds.shift();
		from += 1;
	}
	if (bounds.length > 0 && bounds[bounds.length - 1] === to - 1) {
		bounds.pop();
		to -= 1;
	}
	const cells: [number, number][] = [];
	let at = from;
	for (const b of bounds) {
		cells.push([at, b]);
		at = b + 1;
	}
	cells.push([at, to]);
	return cells;
}

/** The delimiter row's alignments, or null when `text` is not one. */
function delimiterRow(text: string): Align[] | null {
	if (pipes(text).length === 0 || isBlockStart(text)) return null;
	const out: Align[] = [];
	for (const [from, to] of rowCells(text)) {
		const m = DELIM_CELL.exec(text.slice(from, to).trim());
		if (!m) return null;
		out.push(m[1] && m[2] ? "center" : m[2] ? "right" : m[1] ? "left" : null);
	}
	return out;
}

/**
 * The alignments when lines[i] and lines[i + 1] open a table, else null: a
 * header line with a pipe, then a delimiter row with as many cells.
 */
function tableAt(lines: Line[], i: number): Align[] | null {
	const head = lines[i]?.text;
	const next = lines[i + 1]?.text;
	if (head === undefined || next === undefined) return null;
	if (pipes(head).length === 0 || isBlockStart(head)) return null;
	const aligns = delimiterRow(next);
	if (!aligns || aligns.length !== rowCells(head).length) return null;
	return aligns;
}

type ListKind = "bullet" | "ordered" | "task";

function listKind(text: string): ListKind | null {
	if (TASK.test(text)) return "task";
	if (BULLET.test(text)) return "bullet";
	if (ORDERED.test(text)) return "ordered";
	return null;
}

function leadingWs(text: string): number {
	const m = /^[ \t]*/.exec(text);
	return m ? m[0].length : 0;
}

function isBlockStart(text: string): boolean {
	return (
		RULE.test(text) ||
		HEADING.test(text) ||
		FENCE.test(text) ||
		QUOTE.test(text) ||
		BULLET.test(text) ||
		ORDERED.test(text)
	);
}

/* ============================== public types ============================= */

/** A parsed text node's span in the markdown source, in document order. */
type Anchor = { from: number; to: number };

/**
 * A source-offset -> document-position map, in document order. Only needed to
 * put the caret at an exact source offset; everything else addresses the
 * document directly.
 */
export type SourceMap = { src: Anchor; pos: number; size: number }[];

export type Parsed = { doc: PMNode; map: SourceMap };

export type Markdown = {
	parseMarkdown: (source: string) => Parsed;
	serializeMarkdown: (doc: PMNode) => string;
	serializeRange: (doc: PMNode, from: number, to: number) => string;
	posForOffset: (parsed: Parsed, offset: number) => number;
};

/* ============================== factory ================================== */

/**
 * Bind the parser / serializer pair to one schema. Both directions name node
 * and mark types directly, so they cannot be schema-agnostic; a closure is
 * how they stay a matched pair instead of two modules that have to agree on a
 * singleton.
 */
export function createMarkdown(s: ProseSchema): Markdown {
	const { schema, nodeType, markType } = s;

	/* --- parse --- */

	type Ctx = { anchors: Anchor[] };

	function scanInline(src: Src, marks: readonly Mark[], out: PMNode[], ctx: Ctx): void {
		let buf = "";
		let bufFrom = -1;
		let bufTo = -1;

		const flush = () => {
			if (!buf) return;
			out.push(schema.text(buf, marks as Mark[]));
			ctx.anchors.push({ from: bufFrom, to: bufTo });
			buf = "";
			bufFrom = -1;
		};
		const take = (ch: string, at: number) => {
			if (bufFrom < 0) bufFrom = at;
			bufTo = at + 1;
			buf += ch;
		};

		let i = 0;
		while (i < src.text.length) {
			const c = src.text[i];

			if (c === "\\" && i + 1 < src.text.length && ESCAPABLE.test(src.text[i + 1])) {
				take(src.text[i + 1], src.map[i]);
				i += 2;
				continue;
			}

			const d = matchDelim(src.text, i);
			if (d) {
				flush();
				const inner = sliceSrc(src, d.inner[0], d.inner[1]);
				if (d.kind === "image") {
					// Alt text is plain: escapes resolve, nothing nests.
					const alt = inner.text.replace(/\\(.)/g, "$1");
					out.push(nodeType.image.create({ src: d.href, alt }, null, marks as Mark[]));
				} else if (d.kind === "code") {
					// Literal span: no escapes, no nested marks. Backticks are what
					// markdown says they are.
					const mark = markType.code.create();
					out.push(schema.text(inner.text, mark.addToSet(marks as Mark[])));
					ctx.anchors.push({
						from: inner.map[0] ?? src.map[i],
						to: (inner.map[inner.map.length - 1] ?? src.map[i]) + 1,
					});
				} else {
					const mark =
						d.kind === "strong"
							? markType.strong.create()
							: d.kind === "em"
								? markType.em.create()
								: markType.link.create({ href: d.href });
					scanInline(inner, mark.addToSet(marks as Mark[]), out, ctx);
				}
				i = d.next;
				continue;
			}

			take(c, src.map[i]);
			i += 1;
		}
		flush();
	}

	function inlineNodes(lines: Line[], ctx: Ctx): PMNode[] {
		const out: PMNode[] = [];
		scanInline(joinLines(lines), [], out, ctx);
		return out;
	}

	function parseList(
		lines: Line[],
		start: number,
		kind: ListKind,
		ctx: Ctx,
	): { node: PMNode; next: number } {
		const ordered = kind === "ordered";
		const re = kind === "task" ? TASK : ordered ? ORDERED : BULLET;
		const indent = leadingWs(lines[start].text);
		const items: PMNode[] = [];
		let order = 1;
		let i = start;

		while (i < lines.length) {
			// A bullet that turns into a checkbox (or back) ends this list and
			// starts the other kind, so the two never mix in one node.
			if (listKind(lines[i].text) !== kind) break;
			const m = re.exec(lines[i].text);
			if (!m || m[1].length !== indent) break;
			if (ordered && items.length === 0) order = Number(m[2]) || 1;
			const checked = kind === "task" && m[4] !== " ";

			// The body starts after the checkbox, but continuation lines only
			// have to clear the bullet, which is what the serializer indents by.
			const cut = m[0].length;
			const markerLen = kind === "task" ? m[1].length + m[2].length + m[3].length : cut;
			const body: Line[] = [{ text: lines[i].text.slice(cut), at: lines[i].at + cut }];
			i += 1;

			// Continuation: anything indented past the marker belongs to this item.
			while (i < lines.length) {
				const t = lines[i].text;
				if (t.trim() === "") {
					const nxt = lines[i + 1];
					if (nxt && nxt.text.trim() !== "" && leadingWs(nxt.text) >= markerLen) {
						body.push({ text: "", at: lines[i].at });
						i += 1;
						continue;
					}
					break;
				}
				if (leadingWs(t) >= markerLen) {
					body.push({ text: t.slice(markerLen), at: lines[i].at + markerLen });
					i += 1;
					continue;
				}
				break;
			}

			let content = parseBlocks(body, ctx);
			if (content.length === 0) content = [nodeType.paragraph.create()];
			// `list_item` is `paragraph block*`, so an item that opens on a nested
			// list still needs a paragraph to hold the caret.
			if (content[0].type !== nodeType.paragraph) {
				content = [nodeType.paragraph.create(), ...content];
			}
			items.push(
				kind === "task"
					? nodeType.taskItem.create({ checked }, content)
					: nodeType.listItem.create(null, content),
			);
		}

		const type =
			kind === "task" ? nodeType.taskList : ordered ? nodeType.orderedList : nodeType.bulletList;
		return { node: type.create(ordered ? { order } : null, items), next: i };
	}

	/**
	 * One cell's inline content. The row was split on unescaped pipes, so here
	 * `\|` is just a pipe, and it is resolved before the inline scan so it
	 * means a pipe inside code spans too. Edge whitespace is padding.
	 */
	function cellInline(line: Line, from: number, to: number, ctx: Ctx): PMNode[] {
		const text: string[] = [];
		const map: number[] = [];
		for (let k = from; k < to; k++) {
			if (line.text[k] === "\\" && line.text[k + 1] === "|") continue;
			text.push(line.text[k]);
			map.push(line.at + k);
		}
		let a = 0;
		let b = text.length;
		while (a < b && /\s/.test(text[a])) a++;
		while (b > a && /\s/.test(text[b - 1])) b--;
		const out: PMNode[] = [];
		scanInline({ text: text.slice(a, b).join(""), map: map.slice(a, b) }, [], out, ctx);
		return out;
	}

	function parseTable(
		lines: Line[],
		start: number,
		aligns: Align[],
		ctx: Ctx,
	): { node: PMNode; next: number } {
		const row = (line: Line, cell: typeof nodeType.tableCell): PMNode => {
			const spans = rowCells(line.text);
			// Short rows pad with empty cells, long ones lose the extras: the
			// header decides the width.
			const cells = aligns.map((align, k) => {
				const span = spans[k];
				const content = span ? cellInline(line, span[0], span[1], ctx) : [];
				return cell.create({ align }, nodeType.paragraph.create(null, content));
			});
			return nodeType.tableRow.create(null, cells);
		};

		const rows = [row(lines[start], nodeType.tableHeader)];
		let i = start + 2;
		while (i < lines.length && lines[i].text.trim() !== "" && !isBlockStart(lines[i].text)) {
			rows.push(row(lines[i], nodeType.tableCell));
			i += 1;
		}
		return { node: nodeType.table.create(null, rows), next: i };
	}

	function parseBlocks(lines: Line[], ctx: Ctx): PMNode[] {
		const out: PMNode[] = [];
		let i = 0;

		while (i < lines.length) {
			const line = lines[i];

			if (line.text.trim() === "") {
				i += 1;
				continue;
			}

			if (RULE.test(line.text)) {
				out.push(nodeType.rule.create());
				i += 1;
				continue;
			}

			const f = FENCE.exec(line.text);
			if (f) {
				// Everything up to a closing fence of the same character, at least
				// as long, is literal. No closing fence runs to the end, the way
				// commonmark reads it.
				const fence = f[1];
				const close = new RegExp(`^${fence[0] === "`" ? "`" : "~"}{${fence.length},}[ \\t]*$`);
				const body: Line[] = [];
				i += 1;
				while (i < lines.length && !close.test(lines[i].text)) {
					body.push(lines[i]);
					i += 1;
				}
				// Unclosed, the source's own trailing newline is not code.
				if (i >= lines.length) {
					while (body.length > 0 && body[body.length - 1].text.trim() === "") body.pop();
				}
				i += 1;
				const text = body.map((l) => l.text).join("\n");
				const content = text ? [schema.text(text)] : [];
				if (text) {
					const last = body[body.length - 1];
					ctx.anchors.push({ from: body[0].at, to: last.at + last.text.length });
				}
				out.push(nodeType.codeBlock.create({ language: f[2] }, content));
				continue;
			}

			const h = HEADING.exec(line.text);
			if (h) {
				const level = h[1].length;
				const at = line.at + h[0].length - h[2].length;
				out.push(nodeType.heading.create({ level }, inlineNodes([{ text: h[2], at }], ctx)));
				i += 1;
				continue;
			}

			if (QUOTE.test(line.text)) {
				const body: Line[] = [];
				while (i < lines.length && QUOTE.test(lines[i].text)) {
					const cut = QUOTE.exec(lines[i].text)?.[0].length ?? 1;
					body.push({
						text: lines[i].text.slice(cut),
						at: lines[i].at + cut,
					});
					i += 1;
				}
				let inner = parseBlocks(body, ctx);
				if (inner.length === 0) inner = [nodeType.paragraph.create()];
				out.push(nodeType.blockquote.create(null, inner));
				continue;
			}

			const kind = listKind(line.text);
			if (kind) {
				const { node, next } = parseList(lines, i, kind, ctx);
				out.push(node);
				i = next;
				continue;
			}

			const aligns = tableAt(lines, i);
			if (aligns) {
				const { node, next } = parseTable(lines, i, aligns, ctx);
				out.push(node);
				i = next;
				continue;
			}

			const buf: Line[] = [];
			while (
				i < lines.length &&
				lines[i].text.trim() !== "" &&
				!isBlockStart(lines[i].text) &&
				// A table right under a hard-wrapped line starts there, as GFM has it.
				!(buf.length > 0 && tableAt(lines, i))
			) {
				buf.push(lines[i]);
				i += 1;
			}
			out.push(nodeType.paragraph.create(null, inlineNodes(buf, ctx)));
		}

		return out;
	}

	function parseMarkdown(source: string): Parsed {
		const ctx: Ctx = { anchors: [] };
		let blocks = parseBlocks(toLines(source), ctx);
		if (blocks.length === 0) blocks = [nodeType.paragraph.create()];
		const doc = schema.node("doc", null, blocks);

		// Text nodes come out of the parser in document order, so zipping them
		// against a document walk is enough; no bookkeeping during construction.
		const map: SourceMap = [];
		let n = 0;
		doc.descendants((node, pos) => {
			if (!node.isText) return true;
			const src = ctx.anchors[n++];
			if (src) map.push({ src, pos, size: node.nodeSize });
			return false;
		});
		return { doc, map };
	}

	/** Document position for a markdown source offset. Clamped, never throws. */
	function posForOffset(parsed: Parsed, offset: number): number {
		const { doc, map } = parsed;
		if (map.length === 0) return 1;
		for (const entry of map) {
			if (offset < entry.src.from) return entry.pos;
			if (offset <= entry.src.to) {
				return entry.pos + Math.min(offset - entry.src.from, entry.size);
			}
		}
		const last = map[map.length - 1];
		return Math.min(last.pos + last.size, doc.content.size);
	}

	/* --- serialize --- */

	/** Escape only what `matchDelim` would otherwise read back as markup. */
	function escapeInline(text: string): string {
		let out = "";
		let i = 0;
		while (i < text.length) {
			const c = text[i];
			if (c === "\\") {
				out += "\\\\";
				i += 1;
				continue;
			}
			if (matchDelim(text, i)) {
				out += `\\${c}`;
				i += 1;
				continue;
			}
			out += c;
			i += 1;
		}
		return out;
	}

	/** Escape a leading marker so a line of prose is not read back as a block. */
	function escapeLineStart(text: string): string {
		if (RULE.test(text)) return `\\${text}`;
		// `[ ]` is only a checkbox right after a bullet, but escaping it wherever
		// a line opens with it is what keeps a list item's text from turning
		// into one.
		return text.replace(
			/^(#{1,6}[ \t]|[-*+][ \t]|\d+[.)][ \t]|>|```|~~~|\[[ xX]\](?=[ \t]|$))/,
			(m) => `\\${m}`,
		);
	}

	function sameMarks(a: readonly Mark[], b: readonly Mark[]): boolean {
		return a.length === b.length && a.every((m, i) => m.eq(b[i]));
	}

	function openDelim(mark: Mark): string {
		if (mark.type === markType.code) return "`";
		if (mark.type === markType.strong) return "**";
		if (mark.type === markType.em) return "*";
		if (mark.type === markType.link) return "[";
		return "";
	}

	function closeDelim(mark: Mark): string {
		if (mark.type === markType.code) return "`";
		if (mark.type === markType.strong) return "**";
		if (mark.type === markType.em) return "*";
		if (mark.type === markType.link) return `](${String(mark.attrs.href)})`;
		return "";
	}

	/**
	 * Marks are serialized as a stack, not per text node: `**bold *and* more**`
	 * has three runs sharing one strong, and closing and reopening it around
	 * each would emit `**bold ****and***...`, which re-parses as nonsense. Marks
	 * always arrive in schema order, so a common-prefix compare is enough to
	 * decide what stays open.
	 */
	function serializeInline(node: PMNode): string {
		// `raw` runs are already markdown (an image) and never merge or escape.
		const runs: { marks: readonly Mark[]; text: string; raw?: boolean }[] = [];
		node.forEach((child) => {
			if (child.type === nodeType.image) {
				const alt = String(child.attrs.alt).replace(/[[\]\\]/g, "\\$&");
				const src = String(child.attrs.src).replace(/[()\s]/g, encodeURIComponent);
				runs.push({ marks: child.marks, text: `![${alt}](${src})`, raw: true });
				return;
			}
			if (!child.isText || child.text === undefined) return;
			const last = runs[runs.length - 1];
			if (last && !last.raw && sameMarks(last.marks, child.marks)) last.text += child.text;
			else runs.push({ marks: child.marks, text: child.text });
		});

		let out = "";
		let open: Mark[] = [];

		const closeDown = (keep: number) => {
			for (let i = open.length - 1; i >= keep; i--) out += closeDelim(open[i]);
			open = open.slice(0, keep);
		};

		for (const run of runs) {
			let keep = 0;
			while (keep < open.length && keep < run.marks.length && open[keep].eq(run.marks[keep])) {
				keep += 1;
			}
			closeDown(keep);
			for (let i = keep; i < run.marks.length; i++) {
				out += openDelim(run.marks[i]);
				open.push(run.marks[i]);
			}
			const isCode = run.marks.some((m) => m.type === markType.code);
			out += isCode || run.raw ? run.text : escapeInline(run.text);
		}
		closeDown(0);

		return out;
	}

	/** A textblock's inline content as a line of prose: a leading marker is escaped. */
	function serializeLine(node: PMNode): string {
		return escapeLineStart(serializeInline(node));
	}

	/**
	 * A table cell. Never block-escaped, since a cell is never read as a block,
	 * but every pipe is written `\|`, even in code: the parser splits the row
	 * before it reads a cell, and gives `\|` back as `|` before anything else.
	 * Edge whitespace would only be read back as padding, so it is not written.
	 */
	function serializeCell(cell: PMNode | undefined): string {
		if (!cell) return "";
		const parts: string[] = [];
		cell.forEach((block) => {
			if (block.isTextblock) parts.push(serializeInline(block));
		});
		return parts.join(" ").replace(/\|/g, "\\|").trim();
	}

	/** First set alignment down a column: the whole column's, as markdown has it. */
	function columnAlign(rows: (PMNode | undefined)[][], col: number): Align {
		for (const row of rows) {
			const align = row[col]?.attrs.align as Align | undefined;
			if (align) return align;
		}
		return null;
	}

	/**
	 * A table in the one form the parser settles on. Merged cells cannot be
	 * written in markdown and the editor offers no way to make one, but a
	 * spanning cell is still written as itself plus empty cells, so a table
	 * from anywhere keeps its shape.
	 */
	function serializeTable(node: PMNode): string {
		const rows: (PMNode | undefined)[][] = [];
		node.forEach((row) => {
			const cells: (PMNode | undefined)[] = [];
			row.forEach((cell) => {
				cells.push(cell);
				const span = Number(cell.attrs.colspan) || 1;
				for (let k = 1; k < span; k++) cells.push(undefined);
			});
			rows.push(cells);
		});
		const width = Math.max(0, ...rows.map((r) => r.length));
		if (width === 0) return "";
		const line = (cells: string[]) => `| ${cells.join(" | ")} |`;
		const cols = Array.from({ length: width }, (_, c) => c);
		const delim = cols.map((c) => {
			const align = columnAlign(rows, c);
			return align === "center"
				? ":---:"
				: align === "right"
					? "---:"
					: align === "left"
						? ":---"
						: "---";
		});
		return [
			line(cols.map((c) => serializeCell(rows[0][c]))),
			line(delim),
			...rows.slice(1).map((r) => line(cols.map((c) => serializeCell(r[c])))),
		].join("\n");
	}

	function prefixLines(text: string, first: string, rest: string): string {
		return text
			.split("\n")
			.map((l, i) => (i === 0 ? first + l : l === "" ? rest.trimEnd() : rest + l))
			.join("\n");
	}

	function isList(node: PMNode): boolean {
		return (
			node.type === nodeType.bulletList ||
			node.type === nodeType.orderedList ||
			node.type === nodeType.taskList
		);
	}

	/**
	 * Blocks are separated by a blank line. The exception is inside a list item,
	 * where a nested list hangs straight off its parent's line: markdown reads
	 * both forms as the same document, but only the tight one is what anyone
	 * writes, so it is what we emit.
	 */
	function serializeChildren(node: PMNode, tight = false): string {
		const parts: { text: string; list: boolean }[] = [];
		node.forEach((child) => {
			const text = serializeBlock(child);
			if (text !== "") parts.push({ text, list: isList(child) });
		});

		let out = "";
		parts.forEach((part, i) => {
			if (i > 0) {
				const glued = tight && (part.list || parts[i - 1].list);
				out += glued ? "\n" : "\n\n";
			}
			out += part.text;
		});
		return out;
	}

	function serializeBlock(node: PMNode): string {
		switch (node.type) {
			case nodeType.paragraph:
				return serializeLine(node);

			case nodeType.heading:
				return `${"#".repeat(node.attrs.level as number)} ${serializeLine(node)}`;

			case nodeType.table:
				return serializeTable(node);

			case nodeType.rule:
				return "---";

			case nodeType.codeBlock: {
				// The fence outgrows any run of backticks inside, so the body can
				// never close it early.
				const text = node.textContent;
				const longest = Math.max(2, ...(text.match(/`+/g) ?? []).map((r) => r.length));
				const fence = "`".repeat(longest + 1);
				const body = text ? `${text}\n` : "";
				return `${fence}${fenceInfo(String(node.attrs.language))}\n${body}${fence}`;
			}

			case nodeType.blockquote:
				return prefixLines(serializeChildren(node), "> ", "> ");

			case nodeType.bulletList: {
				const items: string[] = [];
				node.forEach((item) => {
					items.push(prefixLines(serializeChildren(item, true), "- ", "  "));
				});
				return items.join("\n");
			}

			case nodeType.taskList: {
				const items: string[] = [];
				node.forEach((item) => {
					const box = item.attrs.checked ? "- [x] " : "- [ ] ";
					items.push(prefixLines(serializeChildren(item, true), box, "  "));
				});
				return items.join("\n");
			}

			case nodeType.orderedList: {
				const start = (node.attrs.order as number) ?? 1;
				const items: string[] = [];
				node.forEach((item, _offset, index) => {
					const marker = `${start + index}. `;
					items.push(prefixLines(serializeChildren(item, true), marker, " ".repeat(marker.length)));
				});
				return items.join("\n");
			}

			default:
				return serializeChildren(node);
		}
	}

	/**
	 * The document as markdown. Empty means empty: a lone empty paragraph is the
	 * resting state of a fresh Ref and must serialize to "", not "\n", or every
	 * new document would arrive dirty.
	 */
	function serializeMarkdown(doc: PMNode): string {
		const body = serializeChildren(doc);
		return body === "" ? "" : `${body}\n`;
	}

	/**
	 * Markdown for a range of the document. `cut` rather than `slice`: a caller
	 * splitting the document is about to hand the halves to two separate Refs,
	 * so a half-open node is fine and schema validation would only get in the
	 * way.
	 */
	function serializeRange(doc: PMNode, from: number, to: number): string {
		return serializeMarkdown(doc.cut(from, to));
	}

	return { parseMarkdown, serializeMarkdown, serializeRange, posForOffset };
}

/* ============================== default binding ========================== */

export const markdown: Markdown = createMarkdown(proseSchema);

export const { parseMarkdown, serializeMarkdown, serializeRange, posForOffset } = markdown;
