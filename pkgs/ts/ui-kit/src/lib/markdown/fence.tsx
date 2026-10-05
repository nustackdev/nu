// Code fences in the prose editor.
//
// A ``` fence in a markdown document is drawn by the kit's one code engine
// (lib/code), the same CodeMirror view that backs a `Code` block, so a fence
// in a document and a sample on a page are the same surface: same colors,
// same font, same box, same copy button. Before this a fence was a bare
// <pre>, which looked like a code block until you typed into it.
//
// ## Who owns the text
//
// ProseMirror does. The fence is a node view, and the CodeMirror inside it is
// a window onto the code_block's text, not a second copy with a life of its
// own. This is ProseMirror's "embedded code editor" recipe
// (prosemirror.net/examples/codemirror): an edit in the fence becomes a
// minimal ProseMirror transaction, a document change becomes a minimal
// CodeMirror change, and an `updating` flag stops the two from echoing each
// other. Because every keystroke is a ProseMirror transaction, everything the
// editor does with edits (dirty tracking, autosave, inbound values, undo)
// works on fences with nothing fence-shaped in it.
//
// So the fence leaves out what would make it a separate editor. No CodeMirror
// history: cmd+z inside a fence is the document's undo, so one undo stack
// runs through the whole page. No save key: cmd+enter leaves the fence into a
// fresh paragraph below, the way ProseMirror's own code blocks do, and saving
// is the editor's quiet moment and blur, as everywhere else in the document.
//
// ## Moving through
//
// The caret crosses the fence edge as if it were text. Arrowing off the first
// or last line of a fence hands the caret back to ProseMirror; arrowing into
// one from a paragraph lands in the CodeMirror view (the `arrowInto`
// keys). Backspace in an empty fence turns it back into a paragraph, which
// undoes a ``` typed by mistake the way you would expect.
//
// ## Read-only
//
// The editor flips read-only without rebuilding, so a fence reads
// `view.editable` on every editor update and swaps one compartment: editing
// keys and a language picker, or a plain read-only view with the copy button.
// The look never changes between the two, same as the rest of the document.
//
// The language is the code_block's `language` attribute, loaded on demand
// like a `Code` block's. A name the kit has no grammar for renders plain and
// is still written back verbatim.

import { EditorState as CMState, Compartment } from "@codemirror/state";
import { EditorView as CMView, type KeyBinding, type ViewUpdate } from "@codemirror/view";
import { exitCode } from "prosemirror-commands";
import { redo, undo } from "prosemirror-history";
import { keymap } from "prosemirror-keymap";
import type { Node as PMNode } from "prosemirror-model";
import { type Command, Plugin, Selection, TextSelection } from "prosemirror-state";
import type { EditorView, NodeView, NodeViewConstructor } from "prosemirror-view";
import { useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CopyButton, codeBlockBox } from "../../components/ui/code";
import {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxInput,
	ComboboxItem,
	ComboboxList,
	ComboboxTrigger,
} from "../../components/ui/combobox";
import { codeBase, codeEditing, codeReading } from "../code/extensions";
import {
	findLanguage,
	type LanguageEntry,
	languageCatalogue,
	loadLanguage,
} from "../code/languages";
import { cn } from "../utils";
import { fenceInfo } from "./markdown";
import type { ProseSchema } from "./schema";

/** The picker's name for no language. Never written to a fence. */
const PLAIN = "plain";

type LanguagePickerProps = {
	value: string;
	onChange: (language: string) => void;
	/** The picker closed; the caret goes back to the code. */
	onClose: () => void;
};

/** Plain (null) and the catalogue, with the fence's current language on top. */
function ordered(current: string): (LanguageEntry | null)[] {
	const top = languageCatalogue.find((entry) => entry.value === current);
	const rest = languageCatalogue.filter((entry) => entry !== top);
	return top ? [top, null, ...rest] : [null, ...rest];
}

/**
 * The fence's language, in the corner where a read-only block has its copy
 * button. Any catalogue language, plain, or whatever was typed: a fence can
 * name a language the kit cannot highlight, and the markdown keeps it.
 */
function LanguagePicker({ value, onChange, onClose }: LanguagePickerProps) {
	const [query, setQuery] = useState("");
	const current = findLanguage(value)?.value ?? value;
	// A fence's language is one word: spaces become hyphens, backticks go.
	const typed = query.trim().replace(/\s+/g, "-").replace(/`/g, "");
	const key = typed.toLowerCase();
	const custom = typed !== "" && key !== PLAIN && findLanguage(key) === null;
	return (
		<Combobox
			value={current || PLAIN}
			onValueChange={(next) => onChange(next === PLAIN ? "" : next)}
			onOpenChange={(open) => {
				if (!open) setQuery("");
			}}
		>
			<ComboboxTrigger
				size="sm"
				variant="ghost"
				aria-label="Code language"
				className="w-auto font-mono text-xs text-text-muted"
				// Opens on click; keeping the press from moving focus keeps the caret.
				onMouseDown={(e) => e.preventDefault()}
			>
				<span>{value || PLAIN}</span>
			</ComboboxTrigger>
			<ComboboxContent
				align="end"
				className="w-52"
				onCloseAutoFocus={(e) => {
					e.preventDefault();
					onClose();
				}}
			>
				<ComboboxInput placeholder="Language" value={query} onValueChange={setQuery} />
				<ComboboxList>
					<ComboboxEmpty>No language</ComboboxEmpty>
					{custom && <ComboboxItem value={typed}>Use {typed}</ComboboxItem>}
					{/* The current language first, where the highlight opens. */}
					{ordered(current).map((entry) =>
						entry === null ? (
							<ComboboxItem key={PLAIN} value={PLAIN}>
								plain
							</ComboboxItem>
						) : (
							<ComboboxItem key={entry.value} value={entry.value} keywords={[...entry.aliases]}>
								{entry.label}
							</ComboboxItem>
						),
					)}
				</ComboboxList>
			</ComboboxContent>
		</Combobox>
	);
}

class FenceView implements NodeView {
	dom: HTMLElement;
	cm: CMView;
	private node: PMNode;
	private readonly view: EditorView;
	private readonly getPos: () => number | undefined;
	private readonly schema: ProseSchema;
	private readonly forget: () => void;
	/** Set while a ProseMirror change is being applied to CodeMirror, so it is not sent back. */
	private updating = false;
	private editable: boolean;
	private readonly mode = new Compartment();
	private readonly grammar = new Compartment();
	/** Drops a grammar that arrives after the fence moved on to another language. */
	private ticket = 0;
	private readonly chrome: HTMLElement;
	private readonly root: Root;
	/** What the chrome last drew, so a keystroke does not re-render it. */
	private drawn = "";

	constructor(
		node: PMNode,
		view: EditorView,
		getPos: () => number | undefined,
		schema: ProseSchema,
		forget: () => void,
	) {
		this.node = node;
		this.view = view;
		this.getPos = getPos;
		this.schema = schema;
		this.forget = forget;
		this.editable = view.editable;

		this.dom = document.createElement("div");
		this.dom.setAttribute("data-slot", "code-fence");
		// `my-3` is the gap a fence keeps from its neighbours, what Prose gave a <pre>.
		// The rest undoes what the document would hand down and a `Code` block on
		// a page never gets: the prose tracking, and the wrapping rules the
		// contenteditable needs for its own text.
		this.dom.className = cn(
			codeBlockBox,
			"my-3 tracking-normal whitespace-normal [overflow-wrap:normal]",
		);

		this.cm = new CMView({
			parent: this.dom,
			state: CMState.create({
				doc: node.textContent,
				extensions: [
					this.mode.of(this.modeFor(this.editable)),
					this.grammar.of([]),
					codeBase,
					CMView.updateListener.of((u) => this.forwardUpdate(u)),
					// Keyboard focus (tab, the picker closing) moves no caret, so no
					// update carries the selection over; without this ProseMirror's
					// selection could still be outside and cmd+enter would not exit.
					CMView.domEventHandlers({ focus: () => this.forwardSelection() }),
				],
			}),
		});

		this.chrome = document.createElement("div");
		this.chrome.contentEditable = "false";
		this.chrome.setAttribute("data-fence-chrome", "");
		this.dom.appendChild(this.chrome);
		this.root = createRoot(this.chrome);

		this.stamp();
		this.loadGrammar();
		this.render();
	}

	// -- CodeMirror -> ProseMirror --------------------------------------------

	private forwardUpdate(u: ViewUpdate): void {
		if (this.updating) return;
		const pos = this.getPos();
		if (pos === undefined) return;
		// A selection only means something while the caret is in here; a text
		// change always has to land, or the two copies part ways.
		const focused = this.cm.hasFocus;
		if (!u.docChanged && !focused) return;
		let offset = pos + 1;
		const { main } = u.state.selection;
		const anchor = offset + main.anchor;
		const head = offset + main.head;
		const pmSel = this.view.state.selection;
		if (!u.docChanged && pmSel.anchor === anchor && pmSel.head === head) return;
		const tr = this.view.state.tr;
		u.changes.iterChanges((fromA, toA, fromB, toB, text) => {
			if (text.length) {
				tr.replaceWith(offset + fromA, offset + toA, this.view.state.schema.text(text.toString()));
			} else {
				tr.delete(offset + fromA, offset + toA);
			}
			offset += toB - fromB - (toA - fromA);
		});
		if (focused) tr.setSelection(TextSelection.create(tr.doc, anchor, head));
		this.view.dispatch(tr);
	}

	private forwardSelection(): void {
		if (this.updating || !this.editable) return;
		const pos = this.getPos();
		if (pos === undefined) return;
		const { anchor, head } = this.cm.state.selection.main;
		const { state } = this.view;
		const selection = TextSelection.create(state.doc, pos + 1 + anchor, pos + 1 + head);
		if (!selection.eq(state.selection)) this.view.dispatch(state.tr.setSelection(selection));
	}

	// -- ProseMirror -> CodeMirror --------------------------------------------

	update(node: PMNode): boolean {
		if (node.type !== this.node.type) return false;
		const language = this.node.attrs.language;
		this.node = node;
		if (node.attrs.language !== language) {
			this.stamp();
			this.loadGrammar();
		}
		this.syncEditable();
		this.render();
		if (this.updating) return true;
		const next = node.textContent;
		const cur = this.cm.state.doc.toString();
		if (next !== cur) {
			// The smallest change that turns one into the other, so the caret
			// and the scroll position survive a remote edit or an undo.
			let start = 0;
			let curEnd = cur.length;
			let nextEnd = next.length;
			while (start < curEnd && cur.charCodeAt(start) === next.charCodeAt(start)) start++;
			while (
				curEnd > start &&
				nextEnd > start &&
				cur.charCodeAt(curEnd - 1) === next.charCodeAt(nextEnd - 1)
			) {
				curEnd--;
				nextEnd--;
			}
			this.updating = true;
			this.cm.dispatch({
				changes: { from: start, to: curEnd, insert: next.slice(start, nextEnd) },
			});
			this.updating = false;
		}
		return true;
	}

	setSelection(anchor: number, head: number): void {
		if (!this.editable) return;
		const size = this.cm.state.doc.length;
		this.cm.focus();
		this.updating = true;
		this.cm.dispatch({
			selection: { anchor: Math.min(anchor, size), head: Math.min(head, size) },
		});
		this.updating = false;
	}

	selectNode(): void {
		if (this.editable) this.cm.focus();
	}

	/** Everything inside the fence is the fence's: CodeMirror's keys, the picker's clicks. */
	stopEvent(): boolean {
		return true;
	}

	/** CodeMirror and React redraw this DOM; none of it is ProseMirror's to read back. */
	ignoreMutation(): boolean {
		return true;
	}

	destroy(): void {
		this.ticket++;
		this.forget();
		this.cm.destroy();
		// Unmounting inside a React commit warns; the view can be torn down in one.
		queueMicrotask(() => this.root.unmount());
	}

	// -- read-only, language, chrome -------------------------------------------

	/** Called on every editor update: the editor flips read-only without a rebuild. */
	syncEditable(): void {
		if (this.view.editable === this.editable) return;
		this.editable = this.view.editable;
		this.stamp();
		this.cm.dispatch({ effects: this.mode.reconfigure(this.modeFor(this.editable)) });
		this.render();
	}

	private modeFor(editable: boolean) {
		return editable ? codeEditing({ keys: this.keys() }) : codeReading;
	}

	private stamp(): void {
		const language = this.node.attrs.language as string;
		if (language) this.dom.setAttribute("data-language", language);
		else this.dom.removeAttribute("data-language");
		this.dom.toggleAttribute("data-editable", this.editable);
	}

	private loadGrammar(): void {
		const ticket = ++this.ticket;
		loadLanguage(this.node.attrs.language as string).then((support) => {
			if (ticket !== this.ticket) return;
			this.cm.dispatch({ effects: this.grammar.reconfigure(support ?? []) });
		});
	}

	private render(): void {
		const language = this.node.attrs.language as string;
		const text = this.editable ? "" : this.node.textContent;
		const key = `${this.editable}\0${language}\0${text}`;
		if (key === this.drawn) return;
		this.drawn = key;
		this.root.render(
			this.editable ? (
				// Sunken like the box, so a long first line runs under it, not through it.
				<div className="absolute top-1 right-1 rounded-md bg-bg-sunken">
					<LanguagePicker
						value={language}
						onChange={(next) => this.setLanguage(next)}
						onClose={() => this.cm.focus()}
					/>
				</div>
			) : (
				<CopyButton text={text} />
			),
		);
	}

	private setLanguage(picked: string): void {
		const pos = this.getPos();
		if (pos === undefined || !this.view.editable) return;
		const language = fenceInfo(picked);
		if (language === this.node.attrs.language) return;
		this.view.dispatch(
			this.view.state.tr.setNodeMarkup(pos, undefined, { ...this.node.attrs, language }),
		);
	}

	// -- keys -------------------------------------------------------------------

	private keys(): KeyBinding[] {
		const view = this.view;
		const exit = () => {
			if (!exitCode(view.state, view.dispatch)) return false;
			view.focus();
			return true;
		};
		return [
			{ key: "ArrowUp", run: () => this.maybeEscape("line", -1) },
			{ key: "ArrowLeft", run: () => this.maybeEscape("char", -1) },
			{ key: "ArrowDown", run: () => this.maybeEscape("line", 1) },
			{ key: "ArrowRight", run: () => this.maybeEscape("char", 1) },
			{ key: "Mod-Enter", run: exit },
			{ key: "Ctrl-Enter", run: exit },
			{ key: "Mod-z", run: () => this.history(undo) },
			{ key: "Mod-y", run: () => this.history(redo) },
			{ key: "Shift-Mod-z", run: () => this.history(redo) },
			{ key: "Backspace", run: () => this.unfence() },
		];
	}

	/**
	 * The document's undo, run from inside the fence. When the step it undoes
	 * was outside, the caret follows it out.
	 */
	private history(command: Command): boolean {
		const view = this.view;
		if (!command(view.state, view.dispatch)) return true;
		const pos = this.getPos();
		const { from, to } = view.state.selection;
		if (pos === undefined || from <= pos || to >= pos + this.node.nodeSize) view.focus();
		return true;
	}

	/** Off the edge of the code, into the document. Anywhere else CodeMirror moves the caret. */
	private maybeEscape(unit: "line" | "char", dir: 1 | -1): boolean {
		const { state } = this.cm;
		const main = state.selection.main;
		if (!main.empty) return false;
		const range = unit === "line" ? state.doc.lineAt(main.head) : main;
		if (dir < 0 ? range.from > 0 : range.to < state.doc.length) return false;
		const pos = this.getPos();
		if (pos === undefined) return false;
		const target = pos + (dir < 0 ? 0 : this.node.nodeSize);
		const selection = Selection.near(this.view.state.doc.resolve(target), dir);
		// Nothing on that side to land on (the fence ends the document): stay.
		if (selection.from > pos && selection.to < pos + this.node.nodeSize) return false;
		this.view.dispatch(this.view.state.tr.setSelection(selection).scrollIntoView());
		this.view.focus();
		return true;
	}

	/** Backspace in an empty fence: it was never code, make it a paragraph again. */
	private unfence(): boolean {
		if (this.cm.state.doc.length > 0) return false;
		const pos = this.getPos();
		if (pos === undefined) return false;
		const { state } = this.view;
		const tr = state.tr.replaceWith(
			pos,
			pos + this.node.nodeSize,
			this.schema.nodeType.paragraph.create(),
		);
		tr.setSelection(TextSelection.create(tr.doc, pos + 1));
		this.view.dispatch(tr.scrollIntoView());
		this.view.focus();
		return true;
	}
}

/**
 * Arrowing from the document into a fence. ProseMirror would put its own
 * caret in the code_block's text; this puts it in the CodeMirror view instead
 * (selecting inside a fence focuses it).
 */
function arrowInto(dir: "up" | "down" | "left" | "right", s: ProseSchema): Command {
	return (state, dispatch, view) => {
		if (!view?.editable || !state.selection.empty || !view.endOfTextblock(dir)) return false;
		const side = dir === "left" || dir === "up" ? -1 : 1;
		const $head = state.selection.$head;
		if ($head.depth === 0) return false;
		const next = Selection.near(state.doc.resolve(side > 0 ? $head.after() : $head.before()), side);
		if (next.$head?.parent.type !== s.nodeType.codeBlock) return false;
		dispatch?.(state.tr.setSelection(next));
		return true;
	};
}

export type CodeFences = {
	/** The arrow keys into a fence, and the read-only flip reaching every fence. */
	plugins: Plugin[];
	nodeViews: Record<string, NodeViewConstructor>;
};

/** Code fences for one editor. Build one per view: it tracks that view's fences. */
export function codeFences(s: ProseSchema): CodeFences {
	const live = new Set<FenceView>();

	const sync = new Plugin({
		view: () => ({
			update: () => {
				for (const fence of live) fence.syncEditable();
			},
		}),
	});

	const arrows = keymap({
		ArrowLeft: arrowInto("left", s),
		ArrowRight: arrowInto("right", s),
		ArrowUp: arrowInto("up", s),
		ArrowDown: arrowInto("down", s),
	});

	return {
		plugins: [arrows, sync],
		nodeViews: {
			[s.nodeType.codeBlock.name]: (node, view, getPos) => {
				const fence: FenceView = new FenceView(node, view, getPos, s, () => live.delete(fence));
				live.add(fence);
				return fence;
			},
		},
	};
}
