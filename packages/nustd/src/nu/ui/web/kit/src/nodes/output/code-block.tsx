// CodeBlockRef -- display-only preformatted code block with optional language label.
//
// Server-owned. A write is a partial merge of {code, language, show_copy}
// into the node's props, which is the default store behaviour, so there is no
// handler. Nil on any key reads back as the class default at render time
// (`""`, `""`, true). `language`, when set to a Shiki-supported grammar,
// drives syntax highlighting inside the primitive; unknown languages render
// as plain text. Composes the kit Code primitive in block mode; the primitive
// owns the copy affordance when `copyable` is set.

import { Code } from "../../components/ui/code";
import { type NodeEntry, type NodeProps, useBoolProp, useStringProp } from "../../tree";

function CodeBlockView({ path }: NodeProps) {
	const code = useStringProp(path, "code");
	const language = useStringProp(path, "language");
	const showCopy = useBoolProp(path, "show_copy", true);
	return (
		<Code block copyable={showCopy} language={language || undefined}>
			{code}
		</Code>
	);
}

export const CodeBlockRef: NodeEntry = { component: CodeBlockView };
