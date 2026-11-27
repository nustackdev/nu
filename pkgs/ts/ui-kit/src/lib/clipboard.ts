// Copy text to the clipboard: the kit's one way to, so every copy works in
// the same places.
//
// `navigator.clipboard` exists only in a secure context (https, localhost).
// Over plain http on a LAN or a tailnet it is undefined, so there the text
// goes through a hidden textarea and `document.execCommand("copy")`, which
// still works from a click. The promise says whether the text got there: a
// copy button shows its "copied" state on true only.

/** Write `text` to the clipboard. Resolves true when it got there. */
export async function copyText(text: string): Promise<boolean> {
	if (typeof window !== "undefined" && window.isSecureContext && navigator.clipboard?.writeText) {
		try {
			await navigator.clipboard.writeText(text);
			return true;
		} catch {
			// Refused (permission, no focus): the old path may still take it.
		}
	}
	return execCopy(text);
}

// The pre-Clipboard-API copy: select the text in an offscreen textarea and
// ask the document to copy the selection. Focus and the reader's selection
// are put back after.
function execCopy(text: string): boolean {
	if (typeof document === "undefined") return false;
	const active = document.activeElement as HTMLElement | null;
	const selection = document.getSelection();
	const range = selection && selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
	const area = document.createElement("textarea");
	area.value = text;
	area.setAttribute("readonly", "");
	// Fixed and offscreen: no scroll jump, and readonly keeps a phone's
	// keyboard down.
	area.style.position = "fixed";
	area.style.top = "0";
	area.style.left = "-9999px";
	area.style.opacity = "0";
	document.body.appendChild(area);
	area.focus();
	area.select();
	area.setSelectionRange(0, text.length);
	let ok = false;
	try {
		ok = document.execCommand("copy");
	} catch {
		ok = false;
	}
	area.remove();
	if (range && selection) {
		selection.removeAllRanges();
		selection.addRange(range);
	}
	active?.focus?.();
	return ok;
}
