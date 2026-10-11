import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
	plugins: [react(), tailwindcss()],
	// Own optimizer cache per dev server when set, so parallel servers never share one.
	cacheDir: process.env.NUDLE_VITE_CACHE || undefined,
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
	build: {
		outDir: "dist",
		emptyOutDir: true,
	},
	server: {
		proxy: {
			"/ws": {
				// The Python server's port; set it to run a dev server against a non-default one.
				target: `ws://localhost:${process.env.NUDLE_WS_PORT || "8080"}`,
				ws: true,
			},
		},
	},
});
