import { Badge, FieldView, useStore } from "@nustackdev/ui-kit";
import { useNudleConnection } from "./connect";
import { activeFields } from "./router";
import { Sidebar } from "./Sidebar";

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

	const pages = page?.pages ?? [];
	const showSidebar = !!page && page.sidebar !== false && pages.length > 1;

	const statusBadge = <Badge variant={variant}>{label}</Badge>;

	// Structural Refs (TitleRef, NavRef, ...) render null but must mount so
	// their slices exist in the store. Keep them out of the body flow.
	const structuralNulls = page?.fields.map((f) => <FieldView key={f.path} field={f} />);

	if (showSidebar && page) {
		return (
			<div className="h-screen flex overflow-hidden">
				{structuralNulls}
				<Sidebar
					indexName={page.name}
					pages={pages}
					structural={page.fields}
					footer={statusBadge}
				/>
				<main className="flex-1 min-w-0 h-full overflow-y-auto overflow-x-auto">
					<div className="mx-auto max-w-5xl p-6">
						{fields ? (
							<div className="flex flex-col gap-6">
								{fields.map((f) => <FieldView key={f.path} field={f} />)}
							</div>
						) : (
							<p className="text-sm text-muted-foreground font-mono">waiting for mount...</p>
						)}
					</div>
				</main>
			</div>
		);
	}

	return (
		<div className="min-h-screen p-6">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-muted-foreground font-mono">nudle</span>
					{statusBadge}
				</div>
				{structuralNulls}
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
