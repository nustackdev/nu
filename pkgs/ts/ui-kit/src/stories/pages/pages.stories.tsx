// Pages: whole pages built from the kit in Python, one story per recipe.
//
// Each story replays the frames a recipe sends when it runs (a recorded
// snapshot, see ./recipes.ts), through the real tree store and node registry,
// so what is on screen is what a nuspace cell running that recipe draws. The
// recipes are Meridian, a made-up network of small observatories, and link
// to each other with in-page anchors here.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { PageStage } from "../refs/harness";
import { type RecipeName, recipeFrames } from "./recipes";

const meta: Meta = {
	title: "Pages",
	parameters: { layout: "fullscreen" },
};

export default meta;

type Story = StoryObj;

function page(name: RecipeName): Story {
	return { render: () => <PageStage root={name} frames={recipeFrames(name)} /> };
}

/** Stat cards with sparklines, a bento of charts, recent frames as page links. */
export const Dashboard = page("dashboard");

/** One instrument: hero with eyebrow, its picture, key facts and actions. */
export const Detail = page("detail");

/** Cards with footer actions, link cards, page links and an empty state. */
export const Catalog = page("catalog");

/** A nav list sidebar beside sections of form fields with their actions. */
export const Settings = page("settings");

/** The product page: display heading, features with icons, calls to action. */
export const Landing = page("landing");
