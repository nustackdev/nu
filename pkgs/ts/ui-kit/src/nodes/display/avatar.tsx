// AvatarRef -- an image, or initials when there is none. STUB: the smallest
// honest draw with the Avatar primitive; the display unit owns size, the
// initials rule and the setters.

import { Avatar, AvatarFallback, AvatarImage } from "../../components/ui/avatar";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

function initials(name: string): string {
	return name
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((word) => word[0])
		.join("");
}

function AvatarView({ path }: NodeProps) {
	const src = useStringProp(path, "src");
	const name = useStringProp(path, "name");
	return (
		<Avatar>
			{src ? <AvatarImage src={src} alt={name} /> : null}
			<AvatarFallback>{initials(name)}</AvatarFallback>
		</Avatar>
	);
}

export const AvatarRef: NodeEntry = { component: AvatarView };
