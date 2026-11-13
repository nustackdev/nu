// Form -- a semantic <form> that stacks its children and owns submit.
//
// A native submit (Enter in a single-line input, a click on a `submit`
// button, cmd+Enter in a multi-line one) sends one notify on the form's path:
// `{event: "submit", values, button}`. `values` is a snapshot of every input
// under the form, nested the way the tree is and keyed by segment, a Field
// standing for its control (./../input/control.ts `gather`). `button` is the
// segment of the submit button that fired, or null for Enter with none. The
// browser's own reload is always blocked. Native constraint validation runs
// first, so a `required` input left empty stops the submit in the browser.
//
// After the notify, `clear_on_submit` puts every input back to its seed, and
// `busy_on_submit` marks the form busy: further submits are dropped and the
// submit buttons spin until the program clears it (`set_busy(False)`).
//
// Ops: `read` answers with the same snapshot (`form.values()`), `reset` puts
// every input back to its seed. Chrome (`title`, `busy`) is plain props,
// merged by the default `write`. Layout (`layout.tsx`): a stack's layers,
// `padding` (0), `gap` (4), `justify`, `align` (stretch), `divided`, the size
// props and the per child maps.

import { OPS } from "@nustackdev/ui-core";
import { useMemo } from "react";
import { Heading } from "../../components/ui/heading";
import { cn } from "../../lib/utils";
import {
	type NodeEntry,
	type NodeProps,
	nodeAt,
	tree,
	useBoolProp,
	useSend,
	useStringProp,
} from "../../tree";
import { EVENTS, FormContext, gather, resetUnder } from "../input/control";
import {
	childHandlers,
	flowClass,
	flowStyle,
	type LayoutDefaults,
	StackChildren,
	useLayout,
} from "./layout";

const DEFAULTS: LayoutDefaults = { gap: 4, padding: 0, justify: "start", align: "stretch" };

function FormView({ path }: NodeProps) {
	const title = useStringProp(path, "title");
	const busy = useBoolProp(path, "busy");
	const layout = useLayout(path, DEFAULTS);
	const send = useSend(path);
	const state = useMemo(() => ({ busy }), [busy]);
	return (
		<FormContext.Provider value={state}>
			<form
				data-nu-form=""
				aria-busy={busy || undefined}
				onSubmit={(e) => {
					e.preventDefault();
					const props = nodeAt(path)?.props ?? {};
					if (props.busy) return;
					const submitter = (e.nativeEvent as SubmitEvent).submitter;
					const button = submitter?.getAttribute("name") || null;
					send(OPS.notify, { event: EVENTS.submit, values: gather(path), button });
					if (props.clear_on_submit) resetUnder(path);
					if (props.busy_on_submit) tree.getState().setProps(path, { busy: true });
				}}
				className={cn("flex flex-col", flowClass(layout, "column"))}
				style={flowStyle(layout)}
			>
				{title ? (
					<Heading as="h3" size="xl" className="mb-2">
						{title}
					</Heading>
				) : null}
				<StackChildren path={path} layout={layout} />
			</form>
		</FormContext.Provider>
	);
}

export const Form: NodeEntry = {
	component: FormView,
	fill: true,
	handlers: {
		...childHandlers,
		read: (ctx) => ctx.send(OPS.read, gather(ctx.path), ctx.frame.id),
		reset: (ctx) => resetUnder(ctx.path),
	},
};
