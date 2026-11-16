// Bytes from the browser to a server, as raw POSTs.
//
// Every byte an upload node moves goes this way, never over the ws: a whole
// file for a pull, a `file.slice(a, b)` for a slice. It is XHR and not fetch
// because only XHR reports upload progress (`xhr.upload.onprogress`). The
// browser streams the body from disk, so a large file never sits in the js
// heap.
//
// A slice goes as one POST (`postBlob`). A pull goes in pieces (`postFile`):
// each piece names its offset, a piece the network dropped is sent again
// after a pause, and the server's answer says how much it has, so a blip
// costs one piece and not the file. The intake's query protocol is in
// `nustd.ui.uploads.intake`.
//
// The answer is the intake's `201 {token, size}`, or one of the upload error
// codes the program side maps to its exceptions. A failed request does not
// say why, so on an error the body is probed: a file changed or moved on
// disk after the pick fails to read (`NotReadableError`), which is
// `unreadable`; a body that still reads means the network dropped.

/** Why a transfer ended without a token. */
export type TransferCode =
	| "unreadable"
	| "too_large"
	| "no_space"
	| "refused"
	| "network"
	| "canceled";

export type TransferResult =
	| { token: string; size: number; error: "" }
	| { token: null; size: number; error: TransferCode };

export type Transfer = {
	/** Settles once, never rejects. */
	done: Promise<TransferResult>;
	/** Stop the request. `done` settles with `canceled`. */
	abort: () => void;
};

/** Whether the bytes of `body` can still be read. */
async function readable(body: Blob): Promise<boolean> {
	try {
		const head = body.slice(0, 1);
		await (typeof head.arrayBuffer === "function"
			? head.arrayBuffer()
			: new Response(head).arrayBuffer());
		return true;
	} catch {
		return false;
	}
}

function tokenOf(text: string): { token: string; size: number } | null {
	try {
		const parsed = JSON.parse(text) as { token?: unknown; size?: unknown };
		if (typeof parsed.token !== "string") return null;
		return { token: parsed.token, size: typeof parsed.size === "number" ? parsed.size : 0 };
	} catch {
		return null;
	}
}

type Sent =
	| { status: number; text: string }
	| { status: 0; text: ""; error: "network" | "canceled" };

/** One raw POST of `body`; settles with the answer, never rejects. */
function send(
	url: string,
	body: Blob,
	onProgress: ((sent: number) => void) | undefined,
	hold: (xhr: XMLHttpRequest) => void,
): Promise<Sent> {
	const xhr = new XMLHttpRequest();
	hold(xhr);
	return new Promise<Sent>((resolve) => {
		xhr.open("POST", url);
		xhr.upload.onprogress = (e) => onProgress?.(e.loaded);
		xhr.onload = () => resolve({ status: xhr.status, text: xhr.responseText });
		xhr.onerror = () => resolve({ status: 0, text: "", error: "network" });
		xhr.ontimeout = () => resolve({ status: 0, text: "", error: "network" });
		xhr.onabort = () => resolve({ status: 0, text: "", error: "canceled" });
		xhr.send(body);
	});
}

/** The error code of an answer that carried no token. */
function codeOf(status: number): TransferCode {
	if (status === 413) return "too_large";
	if (status === 507) return "no_space";
	if (status === 403) return "refused";
	return "network";
}

/**
 * POST `body` to `url` as the raw request body. `onProgress` hears the bytes
 * sent so far and the total, as often as the browser reports them.
 */
export function postBlob(
	url: string,
	body: Blob,
	onProgress?: (sent: number, total: number) => void,
): Transfer {
	let xhr: XMLHttpRequest | null = null;
	const done = send(
		url,
		body,
		(sent) => onProgress?.(sent, body.size),
		(x) => {
			xhr = x;
		},
	).then(async (answer): Promise<TransferResult> => {
		const fail = (error: TransferCode) => ({ token: null, size: body.size, error }) as const;
		if ("error" in answer) {
			if (answer.error === "canceled") return fail("canceled");
			return fail((await readable(body)) ? "network" : "unreadable");
		}
		const ok = answer.status >= 200 && answer.status < 300 ? tokenOf(answer.text) : null;
		if (!ok) return fail(codeOf(answer.status));
		return { token: ok.token, size: ok.size, error: "" };
	});
	return { done, abort: () => xhr?.abort() };
}

export type PieceOptions = {
	/** Bytes per POST. */
	piece?: number;
	/** How many times one piece is sent before the pull fails `network`. */
	tries?: number;
	/** The pause before the first resend, in ms; it doubles each time. */
	wait?: number;
};

/** 16 MiB: small enough that a drop costs little, big enough to stay fast. */
export const PIECE = 16 << 20;

/**
 * POST all of `file` to `url` in pieces of `piece` bytes. `onProgress` hears
 * the bytes the server has plus those of the piece in flight. A piece the
 * network dropped goes again after `wait`, then twice that, up to `tries`
 * times; a file that no longer reads fails `unreadable` at once.
 */
export function postFile(
	url: string,
	file: Blob,
	onProgress?: (sent: number, total: number) => void,
	{ piece = PIECE, tries = 5, wait = 500 }: PieceOptions = {},
): Transfer {
	const total = file.size;
	let xhr: XMLHttpRequest | null = null;
	let stopped = false;
	let wake: (() => void) | null = null;
	const join = url.includes("?") ? "&" : "?";
	const pause = (ms: number) =>
		new Promise<void>((resolve) => {
			const timer = setTimeout(resolve, ms);
			wake = () => {
				clearTimeout(timer);
				resolve();
			};
		});

	const run = async (): Promise<TransferResult> => {
		const fail = (error: TransferCode) => ({ token: null, size: total, error }) as const;
		let token: string | null = null;
		let have = 0;
		let left = tries;
		let delay = wait;
		for (;;) {
			if (stopped) return fail("canceled");
			const end = Math.min(total, have + piece);
			const at = have;
			const query = token ? `token=${token}&offset=${at}&total=${total}` : `total=${total}`;
			const answer = await send(
				`${url}${join}${query}`,
				file.slice(at, end),
				(sent) => onProgress?.(at + sent, total),
				(x) => {
					xhr = x;
				},
			);
			if ("error" in answer) {
				if (answer.error === "canceled" || stopped) return fail("canceled");
				if (!(await readable(file.slice(at, end)))) return fail("unreadable");
				left -= 1;
				if (left <= 0) return fail("network");
				await pause(delay);
				delay *= 2;
				continue;
			}
			const told = tokenOf(answer.text);
			if (answer.status === 409 && told && token) {
				have = told.size; // the server has less than we sent: go on from there
				continue;
			}
			if (!told || answer.status < 200 || answer.status >= 300) {
				return fail(codeOf(answer.status));
			}
			if (answer.status === 201) return { token: told.token, size: told.size, error: "" };
			token = told.token;
			have = told.size;
			left = tries;
			delay = wait;
		}
	};

	return {
		done: run(),
		abort: () => {
			stopped = true;
			xhr?.abort();
			wake?.();
		},
	};
}
