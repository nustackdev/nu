import { describe, expect, it } from "vitest";
import { KEYBOARD_MIN_PX, keyboardInset } from "./on-screen-keyboard";

const view = (height: number, offsetTop = 0, scale = 1) => ({ height, offsetTop, scale });

describe("keyboardInset", () => {
	it("is what the keyboard covers of the layout viewport", () => {
		expect(keyboardInset(844, view(508))).toBe(336);
	});

	it("counts the browser's pan: a scrolled visual viewport covers less", () => {
		expect(keyboardInset(844, view(508, 120))).toBe(216);
	});

	it("is none with no keyboard, or only the bars settling", () => {
		expect(keyboardInset(844, view(844))).toBe(0);
		expect(keyboardInset(844, view(844 - KEYBOARD_MIN_PX + 1))).toBe(0);
		expect(keyboardInset(844, view(844 - KEYBOARD_MIN_PX))).toBe(KEYBOARD_MIN_PX);
	});

	it("is none while pinch-zoomed, or with no visual viewport", () => {
		expect(keyboardInset(844, view(400, 0, 2))).toBe(0);
		expect(keyboardInset(844, null)).toBe(0);
	});
});
