// Global Storybook preview. Boots kit tokens once, wraps every story in the
// same canvas chrome the app uses, and wires the theme toggle onto <html>.

import "../src/index.css";
import type { Preview } from "@storybook/react-vite";
import { withThemeByClassName } from "@storybook/addon-themes";
import React from "react";

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
		(Story) => (
			<div className="min-h-screen bg-bg-canvas text-text-primary font-display">
				<Story />
			</div>
		),
	],
};

export default preview;
