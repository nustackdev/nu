// FileRef -- display-only file by url: one row with its name, size and
// type, opened in a new tab, saved by its download link.
//
// Server-owned. A write is a partial merge of {src, name, size, mime,
// download} into the node's props, which is the default store behaviour, so
// there is no handler. Composes the kit File primitive.

import { File } from "../../components/ui/file";
import { type NodeEntry, type NodeProps, useProp, useStringProp } from "../../tree";

function FileView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const name = useStringProp(path, "name");
	const size = useProp<unknown>(path, "size", null);
	const mime = useStringProp(path, "mime");
	const download = useStringProp(path, "download");
	return (
		<File
			src={src || undefined}
			name={name || undefined}
			size={typeof size === "number" ? size : null}
			mime={mime}
			download={download || undefined}
		/>
	);
}

export const FileRef: NodeEntry = { component: FileView, fill: true };
