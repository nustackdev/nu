import { defineConfig } from "vitest/config";

// The tree store is plain data: no DOM, no React, no socket. Node env is all
// it needs, which is the point of keeping core react-free.
export default defineConfig({
	test: {
		environment: "node",
		include: ["src/**/*.test.ts"],
	},
});
