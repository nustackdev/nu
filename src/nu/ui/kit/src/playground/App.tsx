import { ArrowRight, Github, Package, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";

type Theme = "light" | "dark";

function ThemeToggle({ theme, onChange }: { theme: Theme; onChange: (t: Theme) => void }) {
	return (
		<div className="inline-flex rounded-md border border-border-default p-0.5 bg-elevated">
			{(["light", "dark"] as const).map((t) => (
				<button
					key={t}
					type="button"
					onClick={() => onChange(t)}
					className={`px-3 py-1 text-xs font-medium rounded-sm capitalize transition-colors ${
						theme === t
							? "bg-accent text-accent-fg"
							: "text-fg-secondary hover:text-fg"
					}`}
				>
					{t}
				</button>
			))}
		</div>
	);
}

function Section({
	title,
	description,
	children,
}: {
	title: string;
	description?: string;
	children: React.ReactNode;
}) {
	return (
		<section className="border-t border-border-subtle py-12">
			<div className="mb-6 space-y-1">
				<h2 className="text-xl font-semibold tracking-tight">{title}</h2>
				{description && <p className="text-sm text-fg-secondary">{description}</p>}
			</div>
			{children}
		</section>
	);
}

function Swatch({ name, varName }: { name: string; varName: string }) {
	return (
		<div className="flex flex-col gap-2">
			<div
				className="h-16 rounded-md border border-border-subtle"
				style={{ background: `var(${varName})` }}
			/>
			<div className="space-y-0.5">
				<div className="text-xs font-medium">{name}</div>
				<div className="text-[10.5px] text-fg-muted font-mono">{varName}</div>
			</div>
		</div>
	);
}

const PRIMITIVES = {
	purple: [50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const,
	blue: [50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const,
	gray: [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000] as const,
};

const SEMANTIC = [
	{ group: "surface", swatches: ["--bg-canvas", "--bg-surface", "--bg-elevated", "--bg-sunken"] },
	{ group: "text", swatches: ["--text-primary", "--text-secondary", "--text-muted", "--text-inverse"] },
	{ group: "border", swatches: ["--border-subtle", "--border-default", "--border-strong"] },
	{
		group: "accent (purple)",
		swatches: ["--accent", "--accent-wash", "--accent-soft", "--accent-line", "--accent-hover"],
	},
	{
		group: "accent-2 (blue)",
		swatches: [
			"--accent-2",
			"--accent-2-wash",
			"--accent-2-soft",
			"--accent-2-line",
			"--accent-2-hover",
		],
	},
];

export function App() {
	const [theme, setTheme] = useState<Theme>("dark");

	useEffect(() => {
		document.documentElement.classList.toggle("dark", theme === "dark");
	}, [theme]);

	return (
		<div className="min-h-screen bg-canvas text-fg">
			<div className="mx-auto max-w-5xl px-8 py-16">
				<header className="mb-16 flex items-start justify-between gap-4">
					<div className="space-y-2">
						<div className="flex items-center gap-2 text-xs font-mono text-fg-muted">
							<Package className="size-3" />
							@nustackdev/ui-kit
						</div>
						<h1 className="text-3xl font-semibold tracking-tight">Nustack UI kit</h1>
						<p className="text-sm text-fg-secondary max-w-lg">
							Tokens, primitives, and the ref registry for the nudle web fabric. This page
							is the visual truth of the system; edit tokens in{" "}
							<code className="font-mono text-xs px-1 py-0.5 rounded bg-elevated border border-border-subtle">
								src/index.css
							</code>{" "}
							and everything reflects.
						</p>
					</div>
					<ThemeToggle theme={theme} onChange={setTheme} />
				</header>

				<Section
					title="Primitives"
					description="Raw color scales. Reserved for token authoring; components must never reference these directly."
				>
					<div className="space-y-8">
						{Object.entries(PRIMITIVES).map(([hue, steps]) => (
							<div key={hue}>
								<div className="mb-3 text-xs font-mono uppercase tracking-widest text-fg-muted">
									{hue}
								</div>
								<div className="grid grid-cols-6 md:grid-cols-10 gap-3">
									{steps.map((step) => (
										<Swatch
											key={step}
											name={`${hue}-${step}`}
											varName={`--${hue}-${step}`}
										/>
									))}
								</div>
							</div>
						))}
					</div>
				</Section>

				<Section
					title="Semantic tokens"
					description="Role-named tokens. This is the API that components consume."
				>
					<div className="space-y-8">
						{SEMANTIC.map(({ group, swatches }) => (
							<div key={group}>
								<div className="mb-3 text-xs font-mono uppercase tracking-widest text-fg-muted">
									{group}
								</div>
								<div className="grid grid-cols-2 md:grid-cols-5 gap-3">
									{swatches.map((v) => (
										<Swatch key={v} name={v.replace(/^--/, "")} varName={v} />
									))}
								</div>
							</div>
						))}
					</div>
				</Section>

				<Section title="Button" description="cva-based, six variants, four sizes.">
					<div className="space-y-8">
						<div>
							<div className="mb-3 text-xs font-mono uppercase tracking-widest text-fg-muted">
								variants
							</div>
							<div className="flex flex-wrap gap-3 items-center">
								<Button variant="primary">Primary</Button>
								<Button variant="secondary">Secondary</Button>
								<Button variant="soft">Soft</Button>
								<Button variant="outline">Outline</Button>
								<Button variant="ghost">Ghost</Button>
								<Button variant="link">Link</Button>
							</div>
						</div>

						<div>
							<div className="mb-3 text-xs font-mono uppercase tracking-widest text-fg-muted">
								sizes
							</div>
							<div className="flex flex-wrap gap-3 items-center">
								<Button size="sm">Small</Button>
								<Button size="md">Medium</Button>
								<Button size="lg">Large</Button>
								<Button size="icon" aria-label="More">
									<ArrowRight />
								</Button>
							</div>
						</div>

						<div>
							<div className="mb-3 text-xs font-mono uppercase tracking-widest text-fg-muted">
								with icons
							</div>
							<div className="flex flex-wrap gap-3 items-center">
								<Button>
									<Sparkles />
									Get started
									<ArrowRight />
								</Button>
								<Button variant="outline">
									<Github />
									GitHub
								</Button>
								<Button variant="ghost" disabled>
									Disabled
								</Button>
							</div>
						</div>
					</div>
				</Section>

				<Section title="Badge" description="Compact label pill; token-driven variants.">
					<div className="flex flex-wrap gap-3 items-center">
						<Badge variant="primary">purple</Badge>
						<Badge variant="secondary">blue</Badge>
						<Badge variant="neutral">neutral</Badge>
						<Badge variant="outline">outline</Badge>
					</div>
				</Section>

				<footer className="mt-16 border-t border-border-subtle pt-6 text-xs text-fg-muted font-mono">
					@nustackdev/ui-kit playground
				</footer>
			</div>
		</div>
	);
}
