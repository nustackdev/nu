// TagInputRef -- multi-tag entry field. Browser is source of truth.
//
// Committed tags live on the node as `value: string[]`. Adding or removing a
// tag lands the list and sends `{event: "change"}` at once (./control.ts).
// Enter with text in the draft adds a tag; Enter on an empty draft submits
// (and asks an enclosing Form to submit). The store answers a read from
// `value`.
//
// The write handler is here because a list value is not what the default
// write does: nil clears to [], a list replaces wholesale with every item
// stringified, a map merges chrome, and any other scalar is ignored rather
// than stomping the tags. `reset` puts the declared tags back. Composes the
// kit TagInput primitive; the primitive owns the draft, commit-on-Enter/comma
// and remove-on-Backspace.

import { Label } from "../../components/ui/field";
import { TagInput } from "../../components/ui/tag-input";
import { type NodeEntry, type NodeProps, useBoolProp, useListProp, useProp } from "../../tree";
import { isEnter, resetHandler, useCommit, useControl } from "./control";

function normalizeTags(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	const out: string[] = [];
	for (const item of raw) {
		if (typeof item === "string") out.push(item);
		else if (item != null) out.push(String(item));
	}
	return out;
}

function TagInputView({ path }: NodeProps) {
	const tags = useListProp<string>(path, "value");
	const rawMax = useProp<unknown>(path, "max_tags", null);
	const maxTags = typeof rawMax === "number" ? rawMax : null;
	const allowDuplicates = useBoolProp(path, "allow_duplicates");
	const c = useControl(path);
	const { pick, submit } = useCommit(path);

	return (
		<div className="flex flex-col gap-1">
			{c.label && (
				<Label htmlFor={c.id} required={c.required} disabled={c.disabled}>
					{c.label}
				</Label>
			)}
			<TagInput
				{...c.aria}
				value={tags}
				size={c.size}
				maxTags={maxTags ?? undefined}
				allowDuplicates={allowDuplicates}
				placeholder={c.placeholder || undefined}
				disabled={c.disabled}
				readOnly={c.readOnly}
				invalid={c.invalid}
				autoFocus={c.autoFocus}
				onKeyDown={(e) => {
					if (!isEnter(e) || e.currentTarget.value !== "") return;
					e.preventDefault();
					submit(e.currentTarget);
				}}
				onValueChange={(next) => {
					if (!c.readOnly) pick(next);
				}}
			/>
		</div>
	);
}

export const TagInputRef: NodeEntry = {
	component: TagInputView,
	fill: true,
	input: { empty: [] },
	handlers: {
		write: (ctx, payload) =>
			ctx.update((props) => {
				if (payload == null) {
					props.value = [];
					return;
				}
				if (Array.isArray(payload)) {
					props.value = normalizeTags(payload);
					return;
				}
				if (typeof payload === "object") {
					Object.assign(props, payload);
					if ("value" in payload) props.value = normalizeTags(props.value);
				}
			}),
		reset: resetHandler,
	},
};
