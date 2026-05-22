import { useEffect } from "react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Badge } from "@/components/ui/badge";
import { decode, encode, type Frame, type MountField } from "./protocol";
import { renderers } from "./refs";
import { useStore } from "./store";

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	disconnected: { label: "disconnected", variant: "destructive" as const },
};

// Renders one field by type, with an error boundary around the component.
function FieldView({ field }: { field: MountField }) {
	const Comp = renderers[field.type];
	if (!Comp) {
		return <div className="text-sm text-destructive font-mono">no renderer for {field.type}</div>;
	}
	return (
		<ErrorBoundary label={`${field.path} (${field.type})`}>
			<Comp path={field.path} />
		</ErrorBoundary>
	);
}

function App() {
	const status = useStore((s) => s.status);
	const page = useStore((s) => s.page);
	const refs = useStore((s) => s.refs);
	const setStatus = useStore((s) => s.setStatus);
	const setSender = useStore((s) => s.setSender);
	const dispatch = useStore((s) => s.dispatch);

	useEffect(() => {
		const ws = new WebSocket(`ws://${window.location.host}/ws`);
		const send = (f: Frame) => {
			if (ws.readyState === WebSocket.OPEN) ws.send(encode(f));
		};
		setSender(send);
		ws.addEventListener("open", () => setStatus("connected"));
		ws.addEventListener("close", () => setStatus("disconnected"));
		ws.addEventListener("message", (event) => {
			const frame = decode(event.data);
			dispatch(frame);
		});
		return () => ws.close();
	}, [setStatus, setSender, dispatch]);

	const { label, variant } = statusConfig[status];

	// Pick the active page: find the structural NavRef slot's current value,
	// then match it against pages by route. If there's no NavRef or no match,
	// fall back to the first page (if any).
	let activeFields: MountField[] | null = null;
	if (page) {
		const pages = page.pages ?? [];
		if (pages.length === 0) {
			activeFields = page.fields;
		} else {
			const navField = page.fields.find((f) => f.type === "NavRef");
			const currentUri = navField ? (refs[navField.path]?.value as string | undefined) : undefined;
			const match = currentUri ? (pages.find((p) => p.route === currentUri) ?? pages[0]) : pages[0];
			activeFields = match.fields;
		}
	}

	return (
		<div className="min-h-screen p-6">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-muted-foreground font-mono">nudle</span>
					<Badge variant={variant}>{label}</Badge>
				</div>
				{/* Structural Refs always render (TitleRef, NavRef -- they output null). */}
				{page?.fields.map((f) => (
					<FieldView key={f.path} field={f} />
				))}
				{activeFields ? (
					<div className="flex flex-col gap-6">
						{activeFields.map((f) => (
							<FieldView key={f.path} field={f} />
						))}
					</div>
				) : (
					<p className="text-sm text-muted-foreground font-mono">waiting for mount...</p>
				)}
			</div>
		</div>
	);
}

export default App;
