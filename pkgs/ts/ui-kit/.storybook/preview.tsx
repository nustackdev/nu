// Global Storybook preview. Boots kit tokens once, wraps every story in the
// same canvas chrome the app uses, and wires the theme toggle onto <html>.

import "./preview.css";
import type { Preview } from "@storybook/react-vite";
import { withThemeByClassName } from "@storybook/addon-themes";
import React from "react";
import { TouchProvider } from "../src/lib/touch";

const preview: Preview = {
	parameters: {
		layout: "fullscreen",
		controls: {
			matchers: {
				color: /(background|color)$/i,
				date: /Date$/i,
			},
		},
		options: {
			storySort: {
				order: [
					"Docs",
					["Home", "Tokens", "Typography", "Space", "Motion"],
					"UI",
					"Kitchen Sink",
					["About", "Controls", "Surfaces", "Feedback", "Navigation", "Overlays", "Charts"],
					"*",
				],
			},
		},
		backgrounds: { disable: true },
	},
	decorators: [
		withThemeByClassName({
			themes: {
				dark: "dark",
				light: "",
			},
			defaultTheme: "dark",
			parentSelector: "html",
		}),
		// Narrow: the story inside a 360px column on a wide page, the width of
		// a desk strip column. Layout follows the component's own width, so it
		// should look like the phone shot with desktop interactions.
		(Story, { globals }) =>
			globals.frame === "narrow" ? (
				<div className="mx-auto my-6 w-[360px] outline outline-1 outline-dashed outline-border-default">
					<Story />
				</div>
			) : (
				<Story />
			),
		// Touch: auto reads the device (lib/touch.ts), on and off force it.
		(Story, { globals }) =>
			globals.touch === "on" || globals.touch === "off" ? (
				<TouchProvider value={globals.touch === "on"}>
					<Story />
				</TouchProvider>
			) : (
				<Story />
			),
		(Story) => (
			<div className="min-h-screen bg-bg-canvas text-text-primary font-display">
				<Story />
			</div>
		),
	],
	globalTypes: {
		touch: {
			description: "Touch mode",
			toolbar: {
				title: "Touch",
				icon: "mobile",
				items: [
					{ value: "auto", title: "Touch: device" },
					{ value: "on", title: "Touch: on" },
					{ value: "off", title: "Touch: off" },
				],
				dynamicTitle: true,
			},
		},
		frame: {
			description: "Frame width",
			toolbar: {
				title: "Frame",
				icon: "component",
				items: [
					{ value: "full", title: "Frame: full" },
					{ value: "narrow", title: "Frame: narrow column" },
				],
				dynamicTitle: true,
			},
		},
	},
	initialGlobals: { touch: "auto", frame: "full" },
};

export default preview;
