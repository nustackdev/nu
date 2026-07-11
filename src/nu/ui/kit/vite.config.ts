// Playground vite config. Serves src/playground/ locally so designers can
// eyeball tokens + primitives with HMR. The kit itself is NOT bundled; the
// npm package ships src/ and consumers pick up TypeScript directly.

import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
	plugins: [react(), tailwindcss()],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
	server: {
		port: 5174,
	},
});
