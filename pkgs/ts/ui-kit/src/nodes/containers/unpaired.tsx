// Unpaired -- the visible notice for children a paired container cannot draw.
//
// Tabs and Accordion draw a body only under an entry with its id; Field draws
// one control. A child at any other place does not draw, and the container
// says so in place, so a wrong id or a
// second control shows up where it went wrong.

import type { Path } from "@nustackdev/ui-core";
import { Text } from "../../components/ui/text";

export function Unpaired({
	path,
	segments,
	why,
}: {
	path: Path;
	segments: readonly string[];
	why: string;
}) {
	if (!segments.length) return null;
	const list = segments.map((s) => JSON.stringify(s)).join(", ");
	return (
		<Text size="xs" tone="danger" mono>
			{path.join(" / ")}: {list} not drawn, {why}
		</Text>
	);
}
