// Html primitive.
//
// Any html document, drawn in a sandboxed iframe through `srcdoc`. Scripts
// run, but without `allow-same-origin` the frame is its own opaque origin: it
// cannot reach the page, its storage or its cookies.
//
// With no `height` the frame follows its content: a small script is put in
// the document that posts its height up on every resize, and the frame takes
// it. A fixed `height` scrolls inside instead.

import * as React from "react";

import { cn } from "../../lib/utils";

const RADIUS_CLASS = {
	none: "rounded-none",
	sm: "rounded-sm",
	md: "rounded-md",
	lg: "rounded-lg",
} as const;

// Posts the document's height to the parent, rounded up so a fractional
// height never leaves a pixel to scroll. Tagged so the parent only takes
// messages it knows; the source window tells frames apart. The frame follows
// the content, so the document itself never scrolls.
const MEASURE = `<style>html{overflow:hidden}</style><script>(()=>{const post=()=>parent.postMessage({nuHtmlHeight:Math.ceil(document.documentElement.getBoundingClientRect().height)},"*");new ResizeObserver(post).observe(document.documentElement);addEventListener("load",post);post();})();</script>`;

function withMeasure(html: string): string {
	const at = html.lastIndexOf("</body>");
	return at < 0 ? html + MEASURE : html.slice(0, at) + MEASURE + html.slice(at);
}

export interface HtmlProps
	extends Omit<React.IframeHTMLAttributes<HTMLIFrameElement>, "srcDoc" | "height" | "title"> {
	html: string;
	// Names the frame for screen readers (a11y.md §4).
	title: string;
	// Fixed height in px. Unset follows the content.
	height?: number | null;
	// Height before the first measure, so the layout does not jump from zero.
	minHeight?: number;
	radius?: keyof typeof RADIUS_CLASS;
	bordered?: boolean;
}

function Html({
	html,
	title,
	height = null,
	minHeight = 48,
	radius = "md",
	bordered = true,
	className,
	style,
	...props
}: HtmlProps) {
	const ref = React.useRef<HTMLIFrameElement>(null);
	const [measured, setMeasured] = React.useState<number | null>(null);
	const auto = height == null;
	// The border is inside the box (border-box), so a measured height gets it on top.
	const edge = bordered ? 2 : 0;

	React.useEffect(() => {
		if (!auto) return;
		const onMessage = (e: MessageEvent) => {
			if (e.source !== ref.current?.contentWindow) return;
			const h = (e.data as { nuHtmlHeight?: unknown } | null)?.nuHtmlHeight;
			if (typeof h === "number" && Number.isFinite(h)) setMeasured(h);
		};
		window.addEventListener("message", onMessage);
		return () => window.removeEventListener("message", onMessage);
	}, [auto]);

	const doc = React.useMemo(() => (auto ? withMeasure(html) : html), [html, auto]);

	return (
		<iframe
			ref={ref}
			data-slot="html"
			title={title}
			srcDoc={doc}
			sandbox="allow-scripts"
			className={cn(
				"block w-full bg-bg-surface",
				bordered && "border border-border-default",
				RADIUS_CLASS[radius],
				className,
			)}
			style={{ height: auto ? (measured ?? minHeight) + edge : height, ...style }}
			{...props}
		/>
	);
}

export { Html };
