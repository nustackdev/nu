// Anonymous nudle launch ping. Fetches `/api/telemetry-config` from the
// Python backend, the one source of truth for the opt-out (the
// ~/.nudle/config.json flag, NUDLE_TELEMETRY, DO_NOT_TRACK, CI) and the only
// holder of the PostHog token, then POSTs one `nudle_opened` event to
// PostHog's capture endpoint directly -- no SDK, no autocapture, no
// background machinery. The backend hands no token while telemetry is off,
// so there is nothing to send with. Skipped in vite dev mode. Never throws.

const OPENED_EVENT = "nudle_opened";

type TelemetryConfig = {
	enabled: boolean;
	distinct_id: string;
	posthog_token: string;
	posthog_host: string;
	product?: string;
	nudle_version?: string | null;
	nu_version?: string;
	python_version?: string;
	platform?: string;
	arch?: string;
};

export async function initTelemetry(): Promise<void> {
	if (import.meta.env.DEV) return;
	try {
		const res = await fetch("/api/telemetry-config");
		if (!res.ok) return;
		const cfg = (await res.json()) as TelemetryConfig;
		if (cfg.enabled !== true || !cfg.posthog_token) return;
		if (!cfg.posthog_host || !cfg.distinct_id) return;
		const payload = {
			api_key: cfg.posthog_token,
			event: OPENED_EVENT,
			distinct_id: cfg.distinct_id,
			properties: {
				product: cfg.product,
				nudle_version: cfg.nudle_version,
				nu_version: cfg.nu_version,
				python_version: cfg.python_version,
				platform: cfg.platform,
				arch: cfg.arch,
			},
		};
		await fetch(`${cfg.posthog_host.replace(/\/$/, "")}/i/v0/e/`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
			credentials: "omit",
		});
	} catch {
		// swallow: telemetry never breaks the app
	}
}
