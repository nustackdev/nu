import type { Meta, StoryObj } from "@storybook/react-vite";
import { BookOpen, Sparkles } from "lucide-react";
import { Quote, QuoteContent, QuoteHeader } from "./quote";
import { Text } from "./text";

function Label({ children }: { children: string }) {
	return (
		<div className="mb-3 font-mono text-xs uppercase tracking-widest text-text-muted">
			{children}
		</div>
	);
}

function Citation() {
	return (
		<Quote>
			<QuoteHeader>
				<div className="flex min-w-0 items-center gap-2">
					<BookOpen className="size-4 shrink-0" />
					<span className="truncate">RFC 9110, section 9.2.2</span>
				</div>
			</QuoteHeader>
			<QuoteContent>
				<Text>
					A request method is considered idempotent if the intended effect on the server of multiple
					identical requests is the same as the effect for a single such request.
				</Text>
			</QuoteContent>
		</Quote>
	);
}

function Trace() {
	return (
		<Quote>
			<QuoteHeader>
				<div className="flex min-w-0 items-center gap-2">
					<Sparkles className="size-4 shrink-0" />
					<span className="truncate">Working</span>
					<Text as="span" size="sm" tone="muted" className="ml-auto shrink-0 font-normal">
						12s ago
					</Text>
				</div>
			</QuoteHeader>
			<QuoteContent>
				<Text>Read the deploy config and the last three runs.</Text>
				<Text>The cache key changed, so the build starts cold.</Text>
			</QuoteContent>
		</Quote>
	);
}

function Note() {
	return (
		<Quote>
			<QuoteContent>
				<Text>A body alone, no header line.</Text>
			</QuoteContent>
		</Quote>
	);
}

export const Default: StoryObj = {
	render: () => (
		<div className="p-8 max-w-md">
			<Citation />
		</div>
	),
};

export const Matrix: StoryObj = {
	render: () => (
		<div className="p-8 space-y-8 max-w-md">
			<div>
				<Label>citation</Label>
				<Citation />
			</div>
			<div>
				<Label>trace</Label>
				<Trace />
			</div>
			<div>
				<Label>body only</Label>
				<Note />
			</div>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Quote",
};

export default meta;
