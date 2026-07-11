// Storybook config for @nustackdev/ui-kit.
// Stories live next to primitives under src/components/ui/*.stories.tsx.
// Foundation MDX docs live under src/stories/*.mdx and reference stories via
// <Canvas of={Story} /> from sibling .stories.tsx files.

import path from "node:path";
import { fileURLToPath } from "node:url";
import type { StorybookConfig } from "@storybook/react-vite";
import tailwindcss from "@tailwindcss/vite";
import { mergeConfig } from "vite";

// ESM equivalent of __dirname so viteFinal's alias resolves relative to
// this config file no matter where Storybook is booted from.
const dirname = path.dirname(fileURLToPath(import.meta.url));

const config: StorybookConfig = {
	stories: [
		"../src/stories/*.mdx",
		"../src/stories/*.stories.@(ts|tsx)",
		"../src/components/ui/*.stories.@(ts|tsx)",
	],
	addons: ["@storybook/addon-docs", "@storybook/addon-a11y", "@storybook/addon-themes"],
	framework: {
		name: "@storybook/react-vite",
		options: {},
	},
	typescript: {
		reactDocgen: "react-docgen-typescript",
	},
	// Set Vite explicitly so Tailwind v4 + @/ alias behave the same whether
	// Storybook is booted here or from the workspace root.
	async viteFinal(base) {
		return mergeConfig(base, {
			plugins: [tailwindcss()],
			resolve: {
				alias: {
					"@": path.resolve(dirname, "../src"),
				},
			},
		});
	},
};

export default config;
