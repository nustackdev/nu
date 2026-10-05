// Find and replace, drawn with the kit.
//
// CodeMirror ships a search panel built from bare <input> and <button>
// elements, which is browser chrome in the middle of a kit surface. Its
// `createPanel` hook hands us the DOM node instead, so the panel here is kit
// `Input`, `Toggle` and `IconButton` mounted into it, while CodeMirror keeps
// owning everything that is not looks: the query state, the match
// highlighting, the commands and the keymap that opens it.
//
// The query lives in the editor state, not in React. Every control writes a
// new `SearchQuery` through `setSearchQuery`, and the panel re-renders when
// the state's query changes, so cmd+f with a selection, or a host driving the
// query from outside, shows up in the fields like a keystroke would.
//
// The two text fields are uncontrolled for that reason. The render that
// follows a keystroke lands a tick later, and a controlled field would be
// reset to the old value in between and drop the caret at the end. Instead
// the DOM keeps what was typed, and a field is only written to when the
// state's text differs from it, which is never the case for a keystroke.

import {
	closeSearchPanel,
	findNext,
	findPrevious,
	getSearchQuery,
	replaceAll,
	replaceNext,
	SearchQuery,
	search,
	setSearchQuery,
} from "@codemirror/search";
import type { EditorState, Extension } from "@codemirror/state";
import type { EditorView, Panel } from "@codemirror/view";
import {
	CaseSensitive,
	ChevronDown,
	ChevronUp,
	Regex,
	Replace,
	ReplaceAll,
	WholeWord,
	X,
} from "lucide-react";
import type * as React from "react";
import { useEffect, useLayoutEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { IconButton } from "../../components/ui/icon-button";
import { Input } from "../../components/ui/input";
import { Toggle } from "../../components/ui/toggle";

/** Past this many matches the count reads "1000+" rather than walking on. */
const COUNT_CAP = 1000;

type QueryFields = {
	search: string;
	replace: string;
	caseSensitive: boolean;
	regexp: boolean;
	wholeWord: boolean;
};

function fields(q: SearchQuery): QueryFields {
	return {
		search: q.search,
		replace: q.replace,
		caseSensitive: q.caseSensitive,
		regexp: q.regexp,
		wholeWord: q.wholeWord,
	};
}

/** "3 of 12", "12", "none", or "" for an empty or broken query. */
function countLabel(state: EditorState, q: SearchQuery): string {
	if (!q.search || !q.valid) return "";
	const head = state.selection.main;
	const cursor = q.getCursor(state);
	let total = 0;
	let current = 0;
	for (let next = cursor.next(); !next.done; next = cursor.next()) {
		total += 1;
		if (next.value.from === head.from && next.value.to === head.to) current = total;
		if (total >= COUNT_CAP) return `${COUNT_CAP}+`;
	}
	if (total === 0) return "none";
	return current ? `${current} of ${total}` : String(total);
}

/** Keep an uncontrolled field in step with state it did not type itself. */
function useSynced(text: string) {
	const ref = useRef<HTMLInputElement | null>(null);
	useLayoutEffect(() => {
		if (ref.current && ref.current.value !== text) ref.current.value = text;
	}, [text]);
	return ref;
}

function SearchBar({ view }: { view: EditorView }) {
	const query = getSearchQuery(view.state);
	const f = fields(query);
	const editable = !view.state.readOnly;
	const findRef = useSynced(f.search);
	const replaceRef = useSynced(f.replace);

	// Opening the panel lands the caret in the find field, text selected, so
	// typing replaces what cmd+f prefilled from the selection.
	useEffect(() => {
		findRef.current?.focus();
		findRef.current?.select();
	}, [findRef]);

	const set = (patch: Partial<QueryFields>) => {
		view.dispatch({ effects: setSearchQuery.of(new SearchQuery({ ...f, ...patch })) });
	};

	const close = () => {
		closeSearchPanel(view);
		view.focus();
	};

	const onFindKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter") {
			e.preventDefault();
			(e.shiftKey ? findPrevious : findNext)(view);
		} else if (e.key === "Escape") {
			e.preventDefault();
			close();
		}
	};

	const onReplaceKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter") {
			e.preventDefault();
			(e.metaKey || e.ctrlKey ? replaceAll : replaceNext)(view);
		} else if (e.key === "Escape") {
			e.preventDefault();
			close();
		}
	};

	return (
		<div className="flex flex-col gap-1.5 p-2 font-display">
			<div className="flex items-center gap-1">
				<Input
					size="sm"
					ref={findRef}
					defaultValue={f.search}
					placeholder="Find"
					aria-label="Find"
					aria-invalid={f.search !== "" && !query.valid}
					// CodeMirror's openSearchPanel focuses and selects the field
					// carrying this attribute when cmd+f is pressed again.
					{...{ "main-field": "true" }}
					onChange={(e) => set({ search: e.target.value })}
					onKeyDown={onFindKey}
					className="w-56"
				/>
				<span className="min-w-14 px-1 text-sm text-text-muted tabular-nums">
					{countLabel(view.state, query)}
				</span>
				<Toggle
					size="sm"
					pressed={f.caseSensitive}
					onPressedChange={(on) => set({ caseSensitive: on })}
					aria-label="Match case"
				>
					<CaseSensitive />
				</Toggle>
				<Toggle
					size="sm"
					pressed={f.wholeWord}
					onPressedChange={(on) => set({ wholeWord: on })}
					aria-label="Whole word"
				>
					<WholeWord />
				</Toggle>
				<Toggle
					size="sm"
					pressed={f.regexp}
					onPressedChange={(on) => set({ regexp: on })}
					aria-label="Regular expression"
				>
					<Regex />
				</Toggle>
				<IconButton
					variant="ghost"
					size="sm"
					aria-label="Previous match"
					onClick={() => findPrevious(view)}
				>
					<ChevronUp />
				</IconButton>
				<IconButton
					variant="ghost"
					size="sm"
					aria-label="Next match"
					onClick={() => findNext(view)}
				>
					<ChevronDown />
				</IconButton>
				<IconButton
					variant="ghost"
					size="sm"
					aria-label="Close"
					onClick={close}
					className="ml-auto"
				>
					<X />
				</IconButton>
			</div>
			{editable && (
				<div className="flex items-center gap-1">
					<Input
						size="sm"
						ref={replaceRef}
						defaultValue={f.replace}
						placeholder="Replace"
						aria-label="Replace"
						onChange={(e) => set({ replace: e.target.value })}
						onKeyDown={onReplaceKey}
						className="w-56"
					/>
					<span className="min-w-14" />
					<IconButton
						variant="ghost"
						size="sm"
						aria-label="Replace"
						onClick={() => replaceNext(view)}
					>
						<Replace />
					</IconButton>
					<IconButton
						variant="ghost"
						size="sm"
						aria-label="Replace all"
						onClick={() => replaceAll(view)}
					>
						<ReplaceAll />
					</IconButton>
				</div>
			)}
		</div>
	);
}

function createPanel(view: EditorView): Panel {
	const dom = document.createElement("div");
	dom.className = "nu-code-search";
	const root = createRoot(dom);
	let live = true;
	const render = () => {
		if (live) root.render(<SearchBar view={view} />);
	};
	render();
	let query = getSearchQuery(view.state);
	let selection = view.state.selection;

	return {
		dom,
		top: false,
		update(u) {
			const next = getSearchQuery(u.state);
			// The count depends on the document and the selection as well as
			// the query, so any of the three moving is a redraw.
			if (!next.eq(query) || u.docChanged || !u.state.selection.eq(selection)) {
				query = next;
				selection = u.state.selection;
				render();
			}
		},
		// Unmounting inside a React commit warns; the panel can close in one.
		destroy: () => {
			live = false;
			queueMicrotask(() => root.unmount());
		},
	};
}

/** CodeMirror search with the kit's panel. */
export function kitSearch(): Extension {
	return search({ createPanel });
}
