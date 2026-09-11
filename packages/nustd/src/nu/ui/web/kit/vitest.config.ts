import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Two shapes of test live here. The markdown round trip is pure data (schema,
// parser, serializer, no DOM); the editor test mounts a real ProseMirror view
// and needs one. jsdom covers both, so there is one project, not two.
//
// The kit has no build config of its own (it ships source), so this is the
// only vite-shaped file in the package.
export default defineConfig({
	plugins: [react()],
	test: {
		environment: "jsdom",
		include: ["src/**/*.test.{ts,tsx}"],
	},
});
