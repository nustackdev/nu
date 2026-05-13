import { useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { decode } from "./protocol";
import { renderers } from "./renderers";
import { useStore } from "./store";

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	disconnected: { label: "disconnected", variant: "destructive" as const },
};

function App() {
	const status = useStore((s) => s.status);
	const page = useStore((s) => s.page);
	const setStatus = useStore((s) => s.setStatus);
	const dispatch = useStore((s) => s.dispatch);

	useEffect(() => {
		const ws = new WebSocket(`ws://${window.location.host}/ws`);
		ws.addEventListener("open", () => setStatus("connected"));
		ws.addEventListener("close", () => setStatus("disconnected"));
		ws.addEventListener("message", (event) => {
			const frame = decode(event.data);
			dispatch(frame);
		});
		return () => ws.close();
	}, [setStatus, dispatch]);

	const { label, variant } = statusConfig[status];

	return (
		<div className="min-h-screen p-6">
			<div className="mx-auto max-w-3xl">
				<div className="mb-4 flex items-center justify-between">
					<span className="text-sm text-muted-foreground font-mono">nudle</span>
					<Badge variant={variant}>{label}</Badge>
				</div>
				{page ? (
					<div className="flex flex-col gap-6">
						{page.fields.map((f) => {
							const Comp = renderers[f.type];
							if (!Comp) {
								return (
									<div key={f.path} className="text-sm text-destructive font-mono">
										no renderer for {f.type}
									</div>
								);
							}
							return <Comp key={f.path} path={f.path} />;
						})}
					</div>
				) : (
					<p className="text-sm text-muted-foreground font-mono">waiting for mount...</p>
				)}
			</div>
		</div>
	);
}

export default App;
