// Public entry for @nustackdev/ui-kit.
//
// The kit ships four surfaces:
//   - refs        : factory + renderer registries for every Ref type
//   - store       : zustand + immer store bound to the wire protocol
//   - components  : primitives (Badge, Card, Switch, ...) and shared shell bits
//   - lib/utils   : the `cn()` helper
//
// Tailwind tokens live in ./index.css; consumers import that separately.

export * from "./refs";
export { useStore } from "./store";
export { cn } from "./lib/utils";
export { ErrorBoundary } from "./components/ErrorBoundary";
export { FieldView } from "./components/FieldView";
export { Badge, badgeVariants } from "./components/ui/badge";
export { Button, buttonVariants } from "./components/ui/button";
export {
	Card,
	CardAction,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "./components/ui/card";
export { Switch } from "./components/ui/switch";
