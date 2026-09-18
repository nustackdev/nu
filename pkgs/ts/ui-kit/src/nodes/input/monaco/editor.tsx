// The code editor.
//
// A Monaco instance over exactly one string. One editor == one source, the
// same deal the prose editor strikes with one markdown document.
//
// ## Saving
//
// Not every keystroke. Cmd+enter is the deliberate save and blur is the
// accidental one, and a commit that round-trips to the same text is dropped.
// `onDirty` is the live read in between, for a host that wants to show an
// unsaved marker.
//
// ## What is deliberately not here
//
// Nothing about neighbours. No arrow-out into a next block, no escape-to-
// parent, no focus protocol. Those only mean something to a host that owns a
// sequence of these, and this editor owns exactly one value. Keys it does not
// bind keep their editor meaning, and `onEditor` hands the live instance up so
// such a host can bind its own on top.

import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { cn } from "../../../lib/utils";
import { type CodeEditor, type KeyboardEvt, KIT_THEME, loadMonaco, type MonacoApi } from "./loader";

const MIN_HEIGHT = 42;
const MAX_HEIGHT = 560;

export type MonacoEditorProps = {
	/** The source. Owned by whoever renders this. */
	value: string;
	/** A Monaco language id. One the kit did not register renders unhighlighted. */
	language?: string;
	readOnly?: boolean;
	/** Persist. Fires on cmd+enter and on blur, and only when the text changed. */
	onCommit: (source: string) => void;
	/** Whether the buffer differs from `value`, on every keystroke. */
	onDirty?: (dirty: boolean) => void;
	/** Auto-fit bounds in px. The editor grows with its content between them. */
	minHeight?: number;
	maxHeight?: number;
	className?: string;
	/**
	 * Handed the live editor on mount and null on teardown. The escape hatch for
	 * a host that needs to bind keys or drive the caret from above.
	 */
	onEditor?: (editor: CodeEditor | null) => void;
};

export function MonacoEditor({
	value,
	language = "python",
	readOnly = false,
	onCommit,
	onDirty,
	minHeight = MIN_HEIGHT,
	maxHeight = MAX_HEIGHT,
	className,
	onEditor,
}: MonacoEditorProps) {
	const hostRef = useRef<HTMLDivElement | null>(null);
	const editorRef = useRef<CodeEditor | null>(null);
	const monacoRef = useRef<MonacoApi | null>(null);
	// Monaco is created a tick after mount and its listeners bind once, so
	// everything they read goes through a ref rather than a closed-over prop.
	const cb = useRef({ onCommit, onDirty, onEditor });
	cb.current = { onCommit, onDirty, onEditor };
	const valueRef = useRef(value);
	valueRef.current = value;
	const seed = useRef({ language, readOnly });
	seed.current = { language, readOnly };
	const bounds = useRef({ minHeight, maxHeight });
	bounds.current = { minHeight, maxHeight };

	const commit = useCallback((editor: CodeEditor) => {
		const next = editor.getValue();
		if (next === valueRef.current) return;
		cb.current.onCommit(next);
	}, []);

	useLayoutEffect(() => {
		let disposed = false;
		let teardown: (() => void) | null = null;

		loadMonaco().then((monaco: MonacoApi) => {
			const host = hostRef.current;
			if (disposed || !host) return;
			monacoRef.current = monaco;

			const editor = monaco.editor.create(host, {
				value: valueRef.current,
				language: seed.current.language,
				readOnly: seed.current.readOnly,
				// One theme name; ./loader restains it in place on a flip.
				theme: KIT_THEME,
				automaticLayout: true,
				minimap: { enabled: false },
				lineNumbers: "on",
				lineNumbersMinChars: 3,
				glyphMargin: false,
				folding: false,
				scrollBeyondLastLine: false,
				renderLineHighlight: "none",
				overviewRulerLanes: 0,
				hideCursorInOverviewRuler: true,
				scrollbar: {
					vertical: "auto",
					horizontal: "auto",
					alwaysConsumeMouseWheel: false,
				},
				padding: { top: 8, bottom: 8 },
				// The kit's base step, so code does not tower over the text next to it.
				fontSize: 13,
				fontFamily:
					getComputedStyle(document.documentElement).getPropertyValue("--font-mono") || "monospace",
				tabSize: 4,
				insertSpaces: true,
				wordWrap: "on",
				contextmenu: false,
				fixedOverflowWidgets: true,
				// Suggestions are off on purpose. Nothing registers a completion
				// provider, so the only thing on offer is word-based noise, and an
				// open suggest widget swallows ArrowUp/ArrowDown from any host that
				// wants them.
				quickSuggestions: false,
				suggestOnTriggerCharacters: false,
				wordBasedSuggestions: "off",
				parameterHints: { enabled: false },
			});
			editorRef.current = editor;

			const fit = () => {
				const { minHeight: lo, maxHeight: hi } = bounds.current;
				const h = Math.min(hi, Math.max(lo, editor.getContentHeight()));
				host.style.height = `${h}px`;
				editor.layout({ width: host.clientWidth, height: h });
			};
			fit();

			const subs = [
				editor.onDidContentSizeChange(fit),
				editor.onDidChangeModelContent(() => {
					cb.current.onDirty?.(editor.getValue() !== valueRef.current);
				}),
				editor.onKeyDown((e: KeyboardEvt) => {
					if (e.keyCode === monaco.KeyCode.Enter && (e.metaKey || e.ctrlKey)) {
						e.preventDefault();
						e.stopPropagation();
						commit(editor);
					}
				}),
				editor.onDidBlurEditorText(() => commit(editor)),
			];

			cb.current.onEditor?.(editor);

			teardown = () => {
				cb.current.onEditor?.(null);
				for (const s of subs) s.dispose();
				editor.getModel()?.dispose();
				editor.dispose();
				editorRef.current = null;
				monacoRef.current = null;
			};
		});

		return () => {
			disposed = true;
			teardown?.();
		};
		// The editor is built once and driven imperatively from here on.
	}, [commit]);

	// Inbound source changed (our own save round-tripped, or someone else wrote
	// it). Last actor wins, but not mid-keystroke: only overwrite a buffer
	// nobody has the caret in.
	useEffect(() => {
		const editor = editorRef.current;
		if (!editor) return;
		if (editor.getValue() !== value && !editor.hasTextFocus()) {
			editor.setValue(value);
			cb.current.onDirty?.(false);
		}
	}, [value]);

	useEffect(() => {
		const model = editorRef.current?.getModel();
		if (!model || !monacoRef.current) return;
		monacoRef.current.editor.setModelLanguage(model, language);
	}, [language]);

	useEffect(() => {
		editorRef.current?.updateOptions({ readOnly });
	}, [readOnly]);

	return (
		<div
			ref={hostRef}
			data-slot="monaco-host"
			className={cn(
				"w-full overflow-hidden rounded-md border border-border-subtle bg-bg-sunken",
				className,
			)}
			style={{ minHeight }}
		/>
	);
}
