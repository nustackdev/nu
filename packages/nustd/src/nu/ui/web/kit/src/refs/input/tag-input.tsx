// TagInputRef -- multi-tag entry field. Browser is source of truth.
//
// Committed tags live on the slice as `value: string[]`. Server write
// replaces the committed list wholesale; nil clears to []. Class-level
// defaults (label, placeholder, value, max_tags, allow_duplicates) seed the
// slice via mount props. Composes the kit TagInput primitive; the primitive
// owns the buffer + commit-on-Enter/comma + remove-on-Backspace behavior.

import { useId } from "react";
import { OP_NOTIFY } from "@nustackdev/ui-core";
import { TagInput } from "../../components/ui/tag-input";
import { useStore } from "../../store";
import type { RefEntry, SliceFactory } from "../types";

function normalizeTags(raw: unknown): string[] {
	if (!Array.isArray(raw)) return [];
	const out: string[] = [];
	for (const item of raw) {
		if (typeof item === "string") out.push(item);
		else if (item != null) out.push(String(item));
	}
	return out;
}

const factory: SliceFactory = (path, ctx, props) => ({
	type: "TagInputRef",
	value: normalizeTags(props?.value),
	label: typeof props?.label === "string" ? (props.label as string) : "",
	placeholder: typeof props?.placeholder === "string" ? (props.placeholder as string) : "",
	maxTags: typeof props?.max_tags === "number" ? (props.max_tags as number) : null,
	allowDuplicates: props?.allow_duplicates === true,
	write: (v) =>
		ctx.set((refs) => {
			const slice = refs[path];
			if (!slice) return;
			if (v == null) {
				slice.value = [];
				return;
			}
			if (!Array.isArray(v)) return;
			slice.value = normalizeTags(v);
		}),
	get: () => {
		const slice = useStore.getState().refs[path];
		return (slice?.value as string[]) ?? [];
	},
});

function TagInputView({ path }: { path: string }) {
	const tags = useStore((s) => (s.refs[path]?.value as string[]) ?? []);
	const label = useStore((s) => (s.refs[path]?.label as string) ?? "");
	const placeholder = useStore((s) => (s.refs[path]?.placeholder as string) ?? "");
	const maxTags = useStore((s) => s.refs[path]?.maxTags as number | null | undefined);
	const send = useStore((s) => s.send);
	const id = useId();

	return (
		<div className="flex flex-col gap-1">
			{label && (
				<label htmlFor={id} className="text-sm font-medium text-text-secondary">
					{label}
				</label>
			)}
			<TagInput
				id={id}
				value={tags}
				maxTags={maxTags ?? undefined}
				placeholder={placeholder || undefined}
				onValueChange={(next) => {
					useStore.setState((draft) => {
						const slice = draft.refs[path];
						if (slice) slice.value = next;
					});
					send({ op: OP_NOTIFY, ref: path, payload: null });
				}}
			/>
		</div>
	);
}

export const TagInputRef: RefEntry = { factory, component: TagInputView };
