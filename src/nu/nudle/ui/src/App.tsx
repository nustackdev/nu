import { useEffect, useState } from "react";

type Status = "connecting" | "connected" | "disconnected";

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

	return (
		<div className="flex h-screen items-center justify-center bg-zinc-950 text-zinc-100">
			<div className="flex flex-col items-center gap-4">
				<h1 className="text-2xl font-semibold tracking-tight">everylens</h1>
				<div className="flex items-center gap-2 text-sm">
					<span
						className={`inline-block h-2 w-2 rounded-full ${
							status === "connected"
								? "bg-emerald-400"
								: status === "connecting"
									? "bg-amber-400"
									: "bg-red-400"
						}`}
					/>
					<span className="text-zinc-400">{status}</span>
				</div>
				{message && <p className="text-sm text-zinc-500">{message}</p>}
			</div>
		</div>
	);
}

export default App;
