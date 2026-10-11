// SpinnerRef -- busy with no known progress (ProgressRef covers known).
//
// Server-owned. A write is a partial merge of `size` / `label` into the
// node's props, which is the default store behaviour, so this type is a
// component and nothing else. Composes the kit Spinner primitive, which is
// the role=status element: `label` is its accessible name ("Loading" when
// empty) and also sits next to it as visible text, hidden from screen
// readers so the status is announced once. An unknown size reads as `md`.

import { Spinner } from "../../components/ui/spinner";
import { Text } from "../../components/ui/text";
import { type NodeEntry, type NodeProps, useStringProp } from "../../tree";

type Size = "sm" | "md" | "lg" | "xl";

const SIZES: Record<string, Size> = { sm: "sm", md: "md", lg: "lg", xl: "xl" };

// The label follows the spinner's weight: small type beside a small
// spinner, body type beside the larger ones.
const LABEL: Record<Size, "xs" | "sm" | "base"> = { sm: "xs", md: "sm", lg: "base", xl: "base" };

function SpinnerView({ path }: NodeProps) {
	const size = SIZES[useStringProp(path, "size", "md")] ?? "md";
	const label = useStringProp(path, "label").trim();
	if (!label) return <Spinner size={size} />;
	return (
		<span data-slot="spinner-node" className="inline-flex items-center gap-2">
			<Spinner size={size} label={label} />
			<Text as="span" size={LABEL[size]} tone="secondary" aria-hidden="true">
				{label}
			</Text>
		</span>
	);
}

export const SpinnerRef: NodeEntry = { component: SpinnerView };
