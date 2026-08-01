// React components keyed by Ref type name.
//
// Split out of index.ts so App-shell code can pull renderers without also
// pulling in the store / factory wiring. The registry lives in factories.ts.

import type { ComponentType } from "react";
import { entries } from "./factories";

export const renderers: Record<string, ComponentType<{ path: string }>> = Object.fromEntries(
	Object.entries(entries).map(([k, e]) => [k, e.component]),
);
