// Typing rules and the empty-document hint.
//
// The input rules are the reason this reads as markdown even though nothing on
// screen is markdown: `# ` becomes a heading as you finish typing the space,
// `- ` starts a list, `**bold**` closes into a mark. The muscle memory people
// already have keeps working, and the source they would have typed is still
// exactly what gets stored.
//
// Deliberately no rule fires on anything the serializer cannot emit. The
// dialect is closed: what you can type, markdown.ts can write back.

import {
	InputRule,
	inputRules,
	textblockTypeInputRule,
	wrappingInputRule,
} from "prosemirror-inputrules";
import type { MarkType } from "prosemirror-model";
import { type EditorState, Plugin, TextSelection } from "prosemirror-state";
import { canJoin, findWrapping } from "prosemirror-transform";
import { Decoration, DecorationSet } from "prosemirror-view";
import type { ProseSchema } from "./schema";

/**
 * `**text**` -> strong, on the closing delimiter. The lookbehind is what keeps
 * `***` from firing the em rule inside a strong run.
 */
function markInputRule(re: RegExp, type: MarkType, s: ProseSchema): InputRule {
	return new InputRule(re, (state, match, start, end) => {
		const inner = match[1];
		if (!inner) return null;
		const existing = state.doc.resolve(start).marks();
		const tr = state.tr.replaceWith(
			start,
			end,
			s.schema.text(inner, type.create().addToSet(existing)),
		);
		// Otherwise the mark stays armed and the next character joins it.
		return tr.removeStoredMark(type);
	});
}

/**
 * `[] `, `[ ] ` or `[x] ` at the start of a line -> a checklist item.
 *
 * On a bare paragraph it wraps it, joining a checklist right above. On the
 * first item of a fresh one-item bullet list (`- ` then `[ ] `, the GFM
 * spelling) it turns that list into a checklist instead of nesting one.
 * Anywhere else it declines and the text stays literal.
 */
function taskInputRule(s: ProseSchema): InputRule {
	const { nodeType } = s;
	return new InputRule(/^\[([ xX]?)\]\s$/, (state, match, start, end) => {
		const checked = match[1] === "x" || match[1] === "X";
		const $start = state.doc.resolve(start);
		const d = $start.depth;

		if (
			d >= 2 &&
			$start.node(d - 1).type === nodeType.listItem &&
			$start.index(d - 1) === 0 &&
			$start.node(d - 2).type === nodeType.bulletList &&
			$start.node(d - 2).childCount === 1
		) {
			const tr = state.tr.delete(start, end);
			const at = $start.before(d - 2);
			const item = tr.doc.nodeAt(at)?.firstChild;
			if (!item) return null;
			const list = nodeType.taskList.create(null, nodeType.taskItem.create({ checked }, item.content));
			tr.replaceWith(at, at + (tr.doc.nodeAt(at)?.nodeSize ?? 0), list);
			// ul, li, p: the caret goes to the start of the item's text.
			return tr.setSelection(TextSelection.create(tr.doc, at + 3));
		}

		const tr = state.tr.delete(start, end);
		const range = tr.doc.resolve(start).blockRange();
		const wrapping = range && findWrapping(range, nodeType.taskList);
		if (!range || !wrapping) return null;
		tr.wrap(
			range,
			wrapping.map((w) => (w.type === nodeType.taskItem ? { type: w.type, attrs: { checked } } : w)),
		);
		const before = tr.doc.resolve(start - 1).nodeBefore;
		if (before?.type === nodeType.taskList && canJoin(tr.doc, start - 1)) tr.join(start - 1);
		return tr;
	});
}

export function proseInputRules(s: ProseSchema): Plugin {
	const { nodeType, markType } = s;
	return inputRules({
		rules: [
			// blocks
			textblockTypeInputRule(/^(#{1,6})\s$/, nodeType.heading, (m) => ({
				level: m[1].length,
			})),
			// ``` or ```python, then a space: the line becomes a code fence
			textblockTypeInputRule(/^```([\w+#.-]*)\s$/, nodeType.codeBlock, (m) => ({
				language: m[1],
			})),
			wrappingInputRule(/^\s*([-+*])\s$/, nodeType.bulletList),
			wrappingInputRule(
				/^(\d+)[.)]\s$/,
				nodeType.orderedList,
				(m) => ({ order: Number(m[1]) }),
				// Only continue an existing list when the numbers line up.
				(m, node) => node.childCount + (node.attrs.order as number) === +m[1],
			),
			wrappingInputRule(/^\s*>\s$/, nodeType.blockquote),
			taskInputRule(s),
			new InputRule(/^(?:---|\*\*\*|___)$/, (state, _m, start, end) =>
				state.tr.replaceRangeWith(start, end, nodeType.rule.create()),
			),
			// marks
			markInputRule(/(?<!\*)\*\*([^*\s](?:[^*]*[^*\s])?)\*\*$/, markType.strong, s),
			markInputRule(/(?<![*\w])\*([^*\s](?:[^*]*[^*\s])?)\*$/, markType.em, s),
			markInputRule(/(?<!`)`([^`]+)`$/, markType.code, s),
		],
	});
}

/* ============================== placeholder ============================== */

function isBlank(state: EditorState, s: ProseSchema): boolean {
	const doc = state.doc;
	if (doc.childCount !== 1) return false;
	const first = doc.firstChild;
	return first != null && first.type === s.nodeType.paragraph && first.content.size === 0;
}

/**
 * The hint on an empty document. A decoration, not a document node: it can
 * never be selected, copied, or serialized, which is the whole reason not to
 * do this with placeholder text in the model.
 *
 * Takes a getter as well as a string so a host can change the hint without
 * tearing the view down and losing the undo stack with it.
 */
export function placeholder(text: string | (() => string), s: ProseSchema): Plugin {
	const read = typeof text === "function" ? text : () => text;
	return new Plugin({
		props: {
			decorations(state) {
				const hint = read();
				if (!hint || !isBlank(state, s)) return null;
				return DecorationSet.create(state.doc, [
					Decoration.node(0, state.doc.firstChild?.nodeSize ?? 2, {
						"data-nu-placeholder": hint,
					}),
				]);
			},
		},
	});
}
