// HtmlRef -- display-only html document in a sandboxed frame.
//
// Server-owned. A write is a partial merge of {html, title, height, bordered}
// into the node's props, which is the default store behaviour, so there is no
// handler. A missing or non-number height follows the content. Composes the
// kit Html primitive.

import { Html } from "../../components/ui/html";
import { type NodeEntry, type NodeProps, useBoolProp, useProp, useStringProp } from "../../tree";

function HtmlView({ path }: NodeProps) {
	const html = useStringProp(path, "html");
	const title = useStringProp(path, "title", "html");
	const raw = useProp<unknown>(path, "height", null);
	const height = typeof raw === "number" && Number.isFinite(raw) ? raw : null;
	const bordered = useBoolProp(path, "bordered", true);
	return <Html html={html} title={title || "html"} height={height} bordered={bordered} />;
}

export const HtmlRef: NodeEntry = { component: HtmlView, fill: true };
