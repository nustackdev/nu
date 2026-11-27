// copyText: the Clipboard API in a secure context, the textarea and
// execCommand path without one (plain http) or when the API refuses, and a
// false when neither takes the text.

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { copyText } from "./clipboard";

const realClipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard");
const realSecure = Object.getOwnPropertyDescriptor(window, "isSecureContext");

function setClipboard(value: unknown) {
	Object.defineProperty(navigator, "clipboard", { value, configurable: true });
}
function setSecure(value: boolean) {
	Object.defineProperty(window, "isSecureContext", { value, configurable: true });
}

let exec: ReturnType<typeof vi.fn>;
let copied: string | null;

beforeEach(() => {
	copied = null;
	// jsdom has no execCommand: stand one in that reads the selected textarea.
	exec = vi.fn((cmd: string) => {
		const el = document.activeElement;
		if (cmd !== "copy" || !(el instanceof HTMLTextAreaElement)) return false;
		copied = el.value;
		return true;
	});
	Object.defineProperty(document, "execCommand", { value: exec, configurable: true });
});

afterEach(() => {
	if (realClipboard) Object.defineProperty(navigator, "clipboard", realClipboard);
	else delete (navigator as { clipboard?: unknown }).clipboard;
	if (realSecure) Object.defineProperty(window, "isSecureContext", realSecure);
	else delete (window as { isSecureContext?: unknown }).isSecureContext;
	delete (document as { execCommand?: unknown }).execCommand;
});

describe("copyText", () => {
	it("writes through the Clipboard API in a secure context", async () => {
		const writeText = vi.fn(() => Promise.resolve());
		setSecure(true);
		setClipboard({ writeText });
		await expect(copyText("hi")).resolves.toBe(true);
		expect(writeText).toHaveBeenCalledWith("hi");
		expect(exec).not.toHaveBeenCalled();
	});

	it("falls back to a textarea and execCommand over plain http", async () => {
		setSecure(false);
		setClipboard(undefined);
		const button = document.createElement("button");
		document.body.appendChild(button);
		button.focus();
		await expect(copyText("over http")).resolves.toBe(true);
		expect(exec).toHaveBeenCalledWith("copy");
		expect(copied).toBe("over http");
		expect(document.querySelector("textarea")).toBeNull();
		expect(document.activeElement).toBe(button);
		button.remove();
	});

	it("falls back when the Clipboard API refuses", async () => {
		setSecure(true);
		setClipboard({ writeText: () => Promise.reject(new Error("denied")) });
		await expect(copyText("again")).resolves.toBe(true);
		expect(copied).toBe("again");
	});

	it("resolves false when nothing takes the text", async () => {
		setSecure(false);
		setClipboard(undefined);
		exec.mockReturnValue(false);
		await expect(copyText("lost")).resolves.toBe(false);
	});
});
