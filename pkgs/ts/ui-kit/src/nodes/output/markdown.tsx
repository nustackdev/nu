// MarkdownRef -- display-only markdown source, rendered as commonmark.
//
// Server-owned, and a write is a full string replace, which is what the
// default store behaviour does with a bare payload: it lands on `value`. So
// this type is a component and nothing else. Nil payload (Nu sentinel) reads
// back as the empty string at render time. No raw html passthrough:
// react-markdown runs without rehype-raw so any <...> in the source renders
// as literal text. Composes the kit Prose primitive; prose styles come from
// tokens, not Tailwind Typography.

import ReactMarkdown from "react-markdown";
import { Prose } from "../../components/ui/prose";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function MarkdownView({ path }: NodeProps) {
	const value = useStringProp(path, "value");
	return (
		<Prose>
			<ReactMarkdown>{value}</ReactMarkdown>
		</Prose>
	);
}

export const MarkdownRef: NodeEntry = { component: MarkdownView };
