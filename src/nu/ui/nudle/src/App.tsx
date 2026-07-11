import { Badge, FieldView, useStore } from "@nustackdev/ui-kit";
import { useNudleConnection } from "./connect";
import { activeFields } from "./router";

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	reconnecting: { label: "reconnecting...", variant: "outline" as const },
	disconnected: { label: "disconnected", variant: "danger" as const },
};

function App() {
	useNudleConnection();
	const status = useStore((s) => s.status);
	const page = useStore((s) => s.page);
	const refs = useStore((s) => s.refs);

	const { label, variant } = statusConfig[status];
	const fields = activeFields(page, refs);

	return (
		<div className="min-h-screen p-6">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-muted-foreground font-mono">nudle</span>
					<Badge variant={variant}>{label}</Badge>
				</div>
				{/* Structural Refs always render (TitleRef, NavRef -- they output null). */}
				{page?.fields.map((f) => <FieldView key={f.path} field={f} />)}
				{fields ? (
					<div className="flex flex-col gap-6">
						{fields.map((f) => <FieldView key={f.path} field={f} />)}
					</div>
				) : (
					<p className="text-sm text-muted-foreground font-mono">waiting for mount...</p>
				)}
			</div>
		</div>
	);
}

export default App;
