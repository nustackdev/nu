import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Status = "connecting" | "connected" | "disconnected";

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	disconnected: { label: "disconnected", variant: "destructive" as const },
} satisfies Record<Status, { label: string; variant: "outline" | "default" | "destructive" }>;

function App() {
	const [status, setStatus] = useState<Status>("connecting");
	const [message, setMessage] = useState("");

	useEffect(() => {
		const ws = new WebSocket(`ws://${window.location.host}/ws`);

		ws.addEventListener("open", () => {
			setStatus("connected");
		});

		ws.addEventListener("message", (event) => {
			const data = JSON.parse(event.data);
			if (data.type === "hello") {
				setMessage(data.message);
			}
		});

		ws.addEventListener("close", () => {
			setStatus("disconnected");
		});

		return () => {
			ws.close();
		};
	}, []);

	const { label, variant } = statusConfig[status];

	return (
		<div className="flex h-screen items-center justify-center">
			<Card className="w-80">
				<CardHeader>
					<CardTitle className="flex items-center justify-between">
						nudle
						<Badge variant={variant}>{label}</Badge>
					</CardTitle>
				</CardHeader>
				{message && (
					<CardContent>
						<p className="text-sm text-muted-foreground font-mono">{message}</p>
					</CardContent>
				)}
			</Card>
		</div>
	);
}

export default App;
