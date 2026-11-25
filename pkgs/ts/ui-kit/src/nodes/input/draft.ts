// Drafts: the text an editor shows before it commits, for a read to answer.
//
// A plain Input puts every keystroke in its `value` prop, so a read sees what
// is under the caret. Code, Markdown and InlineEdit can't: the text lives in
// the editor (CodeMirror, ProseMirror, an open inline field) and `value`
// only moves on a commit. So each of them leaves a way to get its text here,
// by path, on the first edit, and its read answers with it. A read mid-edit
// sees what is typed, the same thing `{event: "input", value}` carries.
//
// The getter reads the editor as it stands, not a copy, so a draft that
// outlives its edits (typed back to the committed text, then blurred: no
// commit goes out) still answers what is on screen. A commit, a cancel or
// the node going away drops it, and the read is back on `value`. Building
// the text costs a serialize, which only a read pays.

import {
	type ErrorPayload,
	type NodeHandler,
	OP_ERROR,
	OPS,
	type Path,
	readField,
} from "@nustackdev/ui-core";
import { pathKey } from "../../tree";

const drafts = new Map<string, () => string>();

/** The node at `path` has edits `read` can see; a read answers with them. */
export function setDraft(path: Path, read: () => string): void {
	drafts.set(pathKey(path), read);
}

/** The node at `path` is back on its `value`: committed, canceled, or gone. */
export function clearDraft(path: Path): void {
	drafts.delete(pathKey(path));
}

/** The text the editor at `path` shows, when it has edits a read should see. */
export function draftAt(path: Path): string | undefined {
	return drafts.get(pathKey(path))?.();
}

/**
 * The `read` handler of a node with a draft and no named reads: the draft
 * while there is one, else `value`. A field read is refused the way the
 * store refuses one for a type that declares none, so the server raises.
 */
export const readDraft: NodeHandler = (ctx, payload) => {
	const field = readField(payload);
	if (field !== "") {
		ctx.send(
			OP_ERROR,
			{
				code: "payload_invalid",
				message: `${ctx.node.type ?? "untyped node"} has no read "${field}"`,
			} satisfies ErrorPayload,
			ctx.frame.id,
		);
		return;
	}
	ctx.send(OPS.read, draftAt(ctx.path) ?? ctx.node.props.value ?? null, ctx.frame.id);
};
