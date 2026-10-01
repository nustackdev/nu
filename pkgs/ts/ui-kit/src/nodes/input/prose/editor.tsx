// The prose editor.
//
// A ProseMirror view over the schema in ./schema.ts, with markdown as the
// only value it ever exposes. One editor == one markdown string.
//
// ## Always live
//
// There is no edit mode. A textarea that swaps to rendered markdown on blur
// means a heading is heading-sized when you read it and 16px when you type in
// it, and clicking puts the caret at the start of whichever line string-matched.
// Both are gone by construction: the same styles apply whether the caret is in
// the document or not, and a contenteditable puts the caret where you clicked.
//
// ## Saving
//
// An always-live editor almost never blurs, so blur alone is not a save story:
// reload the page mid-paragraph and the paragraph is gone. A quiet moment is a
// save point instead. Safe to fire while the caret is here, because a commit
// that round-trips to the same markdown is dropped and an inbound value is
// ignored while the document is dirty.
//
// ## What is deliberately not here
//
// Nothing about neighbours. No split, no merge-up, no arrow-out, no slash
// menu. Those only mean something to a host that owns a sequence of blocks,
// and this editor owns exactly one value. Keys it does not bind are left to
// bubble, so such a host can still act on them from above.

import { baseKeymap, chainCommands, toggleMark } from "prosemirror-commands";
import { history, redo, undo } from "prosemirror-history";
import { keymap } from "prosemirror-keymap";
import { liftListItem, sinkListItem, splitListItem } from "prosemirror-schema-list";
import { DOMSerializer, type Node as PMNode } from "prosemirror-model";
import { type Command, EditorState, type Transaction } from "prosemirror-state";
import { EditorView, type NodeView } from "prosemirror-view";
import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { Checkbox } from "../../../components/ui/checkbox";
import { cn } from "../../../lib/utils";
import { createMarkdown, type Markdown } from "./markdown";
import { placeholder, proseInputRules } from "./rules";
import { type ProseSchema, proseSchema } from "./schema";

/** Quiet-moment autosave. Long enough that a typist never triggers it. */
const SAVE_DELAY = 800;

/**
 * A checklist item: the schema's own `toDOM` for the layout, with the kit's
 * `Checkbox` mounted where the static one goes. The box is not document
 * content, so a click on it is an attribute flip, never a caret move, and it
 * saves like any other edit.
 */
function taskItemView(node: PMNode, view: EditorView, getPos: () => number | undefined): NodeView {
	const spec = node.type.spec.toDOM?.(node);
	if (!spec) throw new Error("task_item has no toDOM");
	const { dom, contentDOM } = DOMSerializer.renderSpec(document, spec);
	const li = dom as HTMLElement;
	const box = li.querySelector("[data-task-box]") as HTMLElement;
	box.replaceChildren();
	const root = createRoot(box);
	let current = node;

	const toggle = () => {
		const pos = getPos();
		if (pos === undefined || !view.editable) return;
		view.dispatch(
			view.state.tr.setNodeMarkup(pos, undefined, {
				...current.attrs,
				checked: !current.attrs.checked,
			}),
		);
	};

	const render = () => {
		li.setAttribute("data-checked", String(current.attrs.checked));
		root.render(
			<Checkbox
				size="sm"
				checked={current.attrs.checked as boolean}
				onCheckedChange={toggle}
				tabIndex={-1}
				aria-label={current.attrs.checked ? "Mark not done" : "Mark done"}
				// Keep the caret where it is: the box is not a place to type.
				onMouseDown={(e) => e.preventDefault()}
			/>,
		);
	};
	render();

	return {
		dom: li,
		contentDOM: contentDOM ?? undefined,
		update(next) {
			if (next.type !== current.type) return false;
			current = next;
			render();
			return true;
		},
		stopEvent: (e) => box.contains(e.target as Node),
		ignoreMutation: (m) =>
			m.type !== "selection" && !(contentDOM?.contains(m.target as Node) ?? false),
		// Unmounting inside a React commit warns; the view can be torn down in one.
		destroy: () => queueMicrotask(() => root.unmount()),
	};
}

export type ProseEditorProps = {
	/** The markdown source. Owned by whoever renders this. */
	value: string;
	placeholder?: string;
	readOnly?: boolean;
	/** Persist. Only fires when the document actually changed. */
	onCommit: (source: string) => void;
	/** Swap the document dialect. Defaults to the kit's own. */
	schema?: ProseSchema;
	className?: string;
	/**
	 * Handed the live view on mount and null on teardown. The escape hatch for
	 * a host that needs to run a ProseMirror command against this document.
	 */
	onView?: (view: EditorView | null) => void;
};

export function ProseEditor({
	value,
	placeholder: hint = "",
	readOnly = false,
	onCommit,
	schema = proseSchema,
	className,
	onView,
}: ProseEditorProps) {
	const hostRef = useRef<HTMLDivElement | null>(null);
	const viewRef = useRef<EditorView | null>(null);
	/** The document changed since the last commit. Gates every write. */
	const dirtyRef = useRef(false);
	/** Pending autosave. */
	const saveTimer = useRef<number | null>(null);
	/** Props change identity every render; the view binds once. */
	const cb = useRef({ value, onCommit, readOnly, hint, onView });
	cb.current = { value, onCommit, readOnly, hint, onView };

	/** The parser / serializer pair for the live schema. */
	const mdRef = useRef<{ schema: ProseSchema; md: Markdown } | null>(null);
	if (mdRef.current?.schema !== schema) {
		mdRef.current = { schema, md: createMarkdown(schema) };
	}
	const md = (): Markdown => (mdRef.current as { schema: ProseSchema; md: Markdown }).md;

	const commit = useCallback((): void => {
		if (saveTimer.current !== null) {
			window.clearTimeout(saveTimer.current);
			saveTimer.current = null;
		}
		if (!dirtyRef.current) return;
		dirtyRef.current = false;
		const view = viewRef.current;
		if (!view) return;
		const next = md().serializeMarkdown(view.state.doc);
		if (next !== cb.current.value) cb.current.onCommit(next);
	}, []);

	const queueSave = useCallback(() => {
		if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
		saveTimer.current = window.setTimeout(() => {
			saveTimer.current = null;
			commit();
		}, SAVE_DELAY);
	}, [commit]);

	useLayoutEffect(() => {
		const host = hostRef.current;
		if (!host) return;

		const { nodeType, markType } = schema;

		const link: Command = (state, dispatch) => {
			const { from, to } = state.selection;
			if (from === to) return false;
			const href = window.prompt("Link to", "https://");
			if (!href) return true;
			dispatch?.(state.tr.addMark(from, to, markType.link.create({ href })));
			return true;
		};

		const editing = keymap({
			Enter: chainCommands(
				splitListItem(nodeType.listItem),
				// A new checklist item starts undone, whatever the one above says.
				splitListItem(nodeType.taskItem, { checked: false }),
				baseKeymap.Enter,
			),
			Tab: chainCommands(sinkListItem(nodeType.listItem), sinkListItem(nodeType.taskItem)),
			"Shift-Tab": chainCommands(liftListItem(nodeType.listItem), liftListItem(nodeType.taskItem)),
			"Mod-b": toggleMark(markType.strong),
			"Mod-i": toggleMark(markType.em),
			"Mod-e": toggleMark(markType.code),
			"Mod-k": link,
			"Mod-z": undo,
			"Mod-y": redo,
			"Shift-Mod-z": redo,
		});

		const state = EditorState.create({
			doc: md().parseMarkdown(cb.current.value).doc,
			plugins: [
				proseInputRules(schema),
				editing,
				keymap(baseKeymap),
				history(),
				placeholder(() => cb.current.hint, schema),
			],
		});

		const view = new EditorView(host, {
			state,
			editable: () => !cb.current.readOnly,
			attributes: { class: "nu-prose-editor", spellcheck: "true" },
			nodeViews: {
				[nodeType.taskItem.name]: (node, v, getPos) => taskItemView(node, v, getPos),
			},
			dispatchTransaction(tr: Transaction) {
				const next = view.state.apply(tr);
				view.updateState(next);
				if (tr.docChanged) {
					dirtyRef.current = true;
					queueSave();
				}
			},
			handleDOMEvents: {
				blur: () => {
					commit();
					return false;
				},
			},
		});
		viewRef.current = view;
		cb.current.onView?.(view);

		return () => {
			cb.current.onView?.(null);
			if (saveTimer.current !== null) window.clearTimeout(saveTimer.current);
			saveTimer.current = null;
			viewRef.current = null;
			view.destroy();
		};
		// The view is built once per schema and driven imperatively from here on.
	}, [commit, queueSave, schema]);

	// -- inbound value -----------------------------------------------------
	//
	// Last actor wins, but not mid-keystroke: an inbound value must never yank
	// text out from under someone who has uncommitted edits. Once the document
	// is clean the server's copy is the truth and gets adopted, caret or no
	// caret.
	useEffect(() => {
		const view = viewRef.current;
		if (!view || dirtyRef.current) return;
		if (md().serializeMarkdown(view.state.doc) === value) return;
		const parsed = md().parseMarkdown(value);
		const tr = view.state.tr.replaceWith(0, view.state.doc.content.size, parsed.doc.content);
		tr.setMeta("addToHistory", false);
		view.dispatch(tr);
	}, [value]);

	// `editable` is a function, so a read-only flip only needs a nudge.
	useEffect(() => {
		viewRef.current?.setProps({ editable: () => !readOnly });
	}, [readOnly]);

	return <div ref={hostRef} className={cn("nu-prose-host", className)} />;
}
