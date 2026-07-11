// Renders one mount field by its Ref type, wrapped in an error boundary.
//
// The renderer registry is name-keyed; a missing type surfaces as a small
// diagnostic instead of a runtime crash. Wrapping each field in a boundary
// keeps a single throwing renderer from blanking the whole page (see
// ErrorBoundary for why).

import type { MountField } from "@nustackdev/ui-core";
import { ErrorBoundary } from "./ErrorBoundary";
import { renderers } from "../refs";

export function FieldView({ field }: { field: MountField }) {
	const Comp = renderers[field.type];
	if (!Comp) {
		return (
			<div className="text-sm text-destructive font-mono">
				no renderer for {field.type}
			</div>
		);
	}
	return (
		<ErrorBoundary label={`${field.path} (${field.type})`}>
			<Comp path={field.path} />
		</ErrorBoundary>
	);
}
