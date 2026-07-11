import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Ladle picks this up automatically. The Tailwind v4 plugin is what turns the
// `@theme inline` block in src/index.css into utility classes at build time.
export default defineConfig({
	plugins: [tailwindcss()],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
});
