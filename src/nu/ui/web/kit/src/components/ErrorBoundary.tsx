// Per-field error boundary.
//
// A renderer that throws during render must not take down the whole page.
// React unmounts the entire root on an uncaught render error; that drops
// `App`, whose effect cleanup closes the ws. So one bad frame would blank
// the page and kill the connection. Wrapping each field in a boundary keeps
// the failure local: a labeled error box, the rest of the page live, the
// ws still open.

import { Component, type ReactNode } from "react";

type Props = { label: string; children: ReactNode };
type State = { message: string | null };

export class ErrorBoundary extends Component<Props, State> {
	state: State = { message: null };

	static getDerivedStateFromError(error: unknown): State {
		return { message: error instanceof Error ? error.message : String(error) };
	}

	render(): ReactNode {
		if (this.state.message !== null) {
			return (
				<div className="rounded border border-destructive/50 bg-destructive/10 p-3 text-sm font-mono text-destructive">
					{this.props.label}: {this.state.message}
				</div>
			);
		}
		return this.props.children;
	}
}
