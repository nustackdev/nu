// Anonymous nudle launch ping. Fetches `/api/telemetry-config` from the
// Python backend (source of truth for the ~/.nu/config.json opt-out flag
// and the PostHog token/host), then POSTs one `nudle_opened` event to
// PostHog's capture endpoint directly -- no SDK, no autocapture, no
// background machinery. Skipped in vite dev mode. Never throws.

type TelemetryConfig = {
	enabled: boolean;
	distinct_id: string;
	posthog_token: string;
	posthog_host: string;
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
		if (!cfg.enabled || !cfg.posthog_token) return;
		const payload = {
			api_key: cfg.posthog_token,
			event: "nudle_opened",
			distinct_id: cfg.distinct_id,
			properties: {
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
			keepalive: true,
		});
	} catch {
		// swallow: telemetry never breaks the app
	}
}
