// Anonymous nudle launch ping, the only telemetry nudle sends. Fetches
// `/api/telemetry-config` from the Python backend, the one source of truth
// for the opt-out (the ~/.nudle/config.json flag, NUDLE_TELEMETRY,
// DO_NOT_TRACK, CI, a dev install) and the only holder of the PostHog
// token, then POSTs one `nudle_opened` event per page load to PostHog's
// capture endpoint directly -- no SDK, no autocapture, no background
// machinery. The backend hands no token or id while telemetry is off, and
// the browser's own Do Not Track / Global Privacy Control signals skip it
// too. Skipped in vite dev mode. Never throws, never blocks rendering.

const OPENED_EVENT = "nudle_opened";
const CAPTURE_PATH = "/i/v0/e/";

type TelemetryConfig = {
	enabled: boolean;
	distinct_id?: string;
	posthog_token?: string;
	posthog_host?: string;
	product?: string;
	nudle_version?: string | null;
	nu_version?: string;
	python_version?: string;
	platform?: string;
	arch?: string;
};

function browserOptedOut(): boolean {
	const nav = navigator as Navigator & { globalPrivacyControl?: boolean };
	return nav.doNotTrack === "1" || nav.globalPrivacyControl === true;
}

let sent = false;

export async function initTelemetry(): Promise<void> {
	if (import.meta.env.DEV || sent) return;
	sent = true;
	try {
		if (browserOptedOut()) return;
		const res = await fetch("/api/telemetry-config", { credentials: "omit" });
		if (!res.ok) return;
		const cfg = (await res.json()) as TelemetryConfig;
		if (cfg.enabled !== true) return;
		const { posthog_token, posthog_host, distinct_id } = cfg;
		if (!posthog_token || !posthog_host || !distinct_id) return;
		const payload = {
			api_key: posthog_token,
			event: OPENED_EVENT,
			distinct_id,
			properties: {
				product: cfg.product ?? "nudle",
				nudle_version: cfg.nudle_version,
				nu_version: cfg.nu_version,
				python_version: cfg.python_version,
				platform: cfg.platform,
				arch: cfg.arch,
			},
		};
		await fetch(`${posthog_host.replace(/\/$/, "")}${CAPTURE_PATH}`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(payload),
			credentials: "omit",
			keepalive: true,
		});
	} catch {
		// swallow: telemetry never breaks the app
	}
}
