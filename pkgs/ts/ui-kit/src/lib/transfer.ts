// Bytes from the browser to a server, as one raw POST.
//
// Every byte an upload node moves goes this way, never over the ws: a whole
// file for a pull, a `file.slice(a, b)` for a slice. It is XHR and not fetch
// because only XHR reports upload progress (`xhr.upload.onprogress`). The
// browser streams the body from disk, so a large file never sits in the js
// heap.
//
// The answer is the intake's `201 {token, size}`, or one of the upload error
// codes the program side maps to its exceptions. A failed request does not
// say why, so on an error the body is probed: a file changed or moved on
// disk after the pick fails to read (`NotReadableError`), which is
// `unreadable`; a body that still reads means the network dropped.

/** Why a transfer ended without a token. */
export type TransferCode = "unreadable" | "too_large" | "refused" | "network" | "canceled";

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

/**
 * POST `body` to `url` as the raw request body. `onProgress` hears the bytes
 * sent so far and the total, as often as the browser reports them.
 */
export function postBlob(
	url: string,
	body: Blob,
	onProgress?: (sent: number, total: number) => void,
): Transfer {
	const xhr = new XMLHttpRequest();
	const done = new Promise<TransferResult>((resolve) => {
		const fail = (error: TransferCode) => resolve({ token: null, size: body.size, error });
		xhr.open("POST", url);
		xhr.upload.onprogress = (e) => {
			onProgress?.(e.loaded, e.lengthComputable ? e.total : body.size);
		};
		xhr.onload = () => {
			if (xhr.status === 413) return fail("too_large");
			if (xhr.status === 403) return fail("refused");
			const answer = xhr.status >= 200 && xhr.status < 300 ? tokenOf(xhr.responseText) : null;
			if (!answer) return fail("network");
			resolve({ token: answer.token, size: answer.size, error: "" });
		};
		xhr.onerror = () => {
			void readable(body).then((ok) => fail(ok ? "network" : "unreadable"));
		};
		xhr.ontimeout = () => fail("network");
		xhr.onabort = () => fail("canceled");
		xhr.send(body);
	});
	return { done, abort: () => xhr.abort() };
}
