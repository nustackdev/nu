import { useEffect } from "react";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Badge } from "@/components/ui/badge";
import { decode, encode, type Frame, type MountField } from "./protocol";
import { renderers } from "./refs";
import { useStore } from "./store";

const statusConfig = {
	connecting: { label: "connecting", variant: "outline" as const },
	connected: { label: "connected", variant: "default" as const },
	reconnecting: { label: "reconnecting...", variant: "outline" as const },
	disconnected: { label: "disconnected", variant: "destructive" as const },
};

// Reconnect: exponential backoff with full jitter, base 250ms, cap 10s.
const BACKOFF_BASE_MS = 250;
const BACKOFF_CAP_MS = 10_000;
// Buffer up to N outbound frames while disconnected; drop oldest beyond N.
// Mostly catches tab-owned notify frames during a reconnect window.
const SEND_QUEUE_MAX = 64;

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
	// `refs` is used to read the NavRef value below.
	const setStatus = useStore((s) => s.setStatus);
	const setSender = useStore((s) => s.setSender);
	const dispatch = useStore((s) => s.dispatch);

	useEffect(() => {
		let ws: WebSocket | null = null;
		let attempts = 0;
		let retryTimer: ReturnType<typeof setTimeout> | null = null;
		let intentionalClose = false;
		const queue: Frame[] = [];

		const flushQueue = () => {
			if (!ws || ws.readyState !== WebSocket.OPEN) return;
			while (queue.length > 0) {
				const f = queue.shift();
				if (f) ws.send(encode(f));
			}
		};

		const send = (f: Frame) => {
			if (ws && ws.readyState === WebSocket.OPEN) {
				ws.send(encode(f));
				return;
			}
			queue.push(f);
			if (queue.length > SEND_QUEUE_MAX) queue.shift();
		};
		setSender(send);

		const scheduleReconnect = () => {
			if (intentionalClose) return;
			attempts += 1;
			const exp = Math.min(BACKOFF_CAP_MS, BACKOFF_BASE_MS * 2 ** (attempts - 1));
			const delay = Math.floor(Math.random() * exp);
			setStatus("reconnecting");
			retryTimer = setTimeout(connect, delay);
		};

		const connect = () => {
			retryTimer = null;
			if (intentionalClose) return;
			setStatus(attempts === 0 ? "connecting" : "reconnecting");
			ws = new WebSocket(`ws://${window.location.host}/ws`);
			ws.binaryType = "arraybuffer";
			ws.addEventListener("open", () => {
				attempts = 0;
				setStatus("connected");
				flushQueue();
			});
			ws.addEventListener("close", (ev) => {
				// Clean close: server said goodbye or we're tearing down. Don't retry.
				if (intentionalClose || ev.code === 1000 || ev.code === 1001) {
					setStatus("disconnected");
					return;
				}
				scheduleReconnect();
			});
			ws.addEventListener("message", (event) => {
				const frame = decode(event.data as ArrayBuffer);
				dispatch(frame);
			});
		};

		connect();

		return () => {
			intentionalClose = true;
			if (retryTimer !== null) clearTimeout(retryTimer);
			if (ws) ws.close(1000, "client teardown");
		};
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
