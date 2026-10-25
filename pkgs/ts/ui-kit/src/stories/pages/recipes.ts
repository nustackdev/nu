// The recipe pages, as Python draws them.
//
// recipes.json is a recorded snapshot: per recipe, the frames its `page()`
// sends, in order, each `{op, ref, payload?, chain}`. The recipes live
// outside the kit (they move to nudemos), so nothing re-records the file
// here: a ref change that the pages should show means re-running them and
// replacing the snapshot.

import type { TreeFrame } from "@nustackdev/ui-core";
import recipes from "./recipes.json";

export type RecipeName = keyof typeof recipes;

/** The frames recipe `name` sends, as the tree store takes them. */
export function recipeFrames(name: RecipeName): TreeFrame[] {
	// An init carries no payload, so the fixture leaves the key out.
	return recipes[name] as unknown as TreeFrame[];
}
