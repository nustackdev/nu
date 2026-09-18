// All primitives at a glance. One default of each so the whole kit reads in
// one scroll.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { ArrowRight, Bell, Search, Star } from "lucide-react";
import { Alert, AlertDescription, AlertIcon, AlertTitle } from "./alert";
import { Avatar, AvatarFallback } from "./avatar";
import { Badge } from "./badge";
import { Button } from "./button";
import { Card, CardContent, CardDescription, CardTitle } from "./card";
import { Checkbox } from "./checkbox";
import { Code } from "./code";
import { Heading } from "./heading";
import { IconButton } from "./icon-button";
import { Input } from "./input";
import { Kbd } from "./kbd";
import { Progress } from "./progress";
import { RadioGroup, RadioGroupItem } from "./radio-group";
import { Separator } from "./separator";
import { Skeleton } from "./skeleton";
import { Slider } from "./slider";
import { Spinner } from "./spinner";
import { Stat, StatDelta, StatLabel, StatValue } from "./stat";
import { StatusPill } from "./status-pill";
import { Switch } from "./switch";
import { Text } from "./text";
import { Toggle } from "./toggle";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
	return (
		<div className="grid grid-cols-[8rem_1fr] items-center gap-4 border-b border-border-subtle py-3">
			<div className="font-mono text-xs text-text-muted">{label}</div>
			<div className="flex flex-wrap items-center gap-3">{children}</div>
		</div>
	);
}

export const All: StoryObj = {
	render: () => (
		<div className="mx-auto max-w-5xl px-8 py-12">
				<Heading as="h1" size="3xl" className="mb-2">
					All primitives
				</Heading>
				<Text size="sm" tone="secondary" className="mb-8">
					One default of each. Open a story from the sidebar for the full matrix.
				</Text>

				<Row label="Button">
					<Button>Primary</Button>
					<Button variant="secondary">Secondary</Button>
					<Button variant="ghost">Ghost</Button>
					<Button variant="destructive">Destructive</Button>
				</Row>
				<Row label="IconButton">
					<IconButton aria-label="Search">
						<Search />
					</IconButton>
					<IconButton variant="secondary" aria-label="Bell">
						<Bell />
					</IconButton>
				</Row>
				<Row label="Input">
					<Input placeholder="Search..." className="w-64" />
				</Row>
				<Row label="Checkbox">
					<Checkbox defaultChecked />
					<Checkbox checked="indeterminate" />
					<Checkbox />
				</Row>
				<Row label="Switch">
					<Switch defaultChecked />
					<Switch />
				</Row>
				<Row label="RadioGroup">
					<RadioGroup defaultValue="a" className="flex gap-4">
						<label className="flex items-center gap-2">
							<RadioGroupItem value="a" />
							<span className="text-sm">A</span>
						</label>
						<label className="flex items-center gap-2">
							<RadioGroupItem value="b" />
							<span className="text-sm">B</span>
						</label>
					</RadioGroup>
				</Row>
				<Row label="Slider">
					<div className="w-48">
						<Slider defaultValue={[40]} />
					</div>
				</Row>
				<Row label="Toggle">
					<Toggle aria-label="Star">
						<Star />
					</Toggle>
					<Toggle defaultPressed aria-label="Star pressed">
						<Star />
					</Toggle>
				</Row>
				<Row label="Badge">
					<Badge>default</Badge>
					<Badge variant="secondary">secondary</Badge>
					<Badge variant="ok">ok</Badge>
					<Badge variant="warn">warn</Badge>
					<Badge variant="danger">danger</Badge>
				</Row>
				<Row label="StatusPill">
					<StatusPill tone="ok">Running</StatusPill>
					<StatusPill tone="warn">Degraded</StatusPill>
					<StatusPill tone="danger">Down</StatusPill>
				</Row>
				<Row label="Progress">
					<div className="w-48">
						<Progress value={60} />
					</div>
				</Row>
				<Row label="Spinner">
					<Spinner size="sm" />
					<Spinner />
					<Spinner size="lg" />
				</Row>
				<Row label="Skeleton">
					<div className="w-48 space-y-1.5">
						<Skeleton shape="text" className="w-3/4" />
						<Skeleton shape="text" className="w-1/2" />
					</div>
				</Row>
				<Row label="Avatar">
					<Avatar>
						<AvatarFallback>GM</AvatarFallback>
					</Avatar>
					<Avatar size="lg">
						<AvatarFallback>AB</AvatarFallback>
					</Avatar>
				</Row>
				<Row label="Kbd">
					<Kbd>⌘</Kbd>
					<Kbd>K</Kbd>
				</Row>
				<Row label="Code">
					<Code>const x = 42</Code>
				</Row>
				<Row label="Text">
					<Text size="base">Body text</Text>
					<Text size="sm" tone="secondary">
						Secondary
					</Text>
				</Row>
				<Row label="Heading">
					<Heading size="lg" as="h4">
						Heading lg
					</Heading>
				</Row>
				<Row label="Separator">
					<div className="w-64">
						<Separator />
					</div>
				</Row>
				<Row label="Card">
					<Card className="w-64">
						<CardContent className="p-4">
							<CardTitle className="mb-1">Card title</CardTitle>
							<CardDescription>Compact card sample.</CardDescription>
						</CardContent>
					</Card>
				</Row>
				<Row label="Alert">
					<div className="w-full max-w-md">
						<Alert tone="info">
							<AlertIcon />
							<div>
								<AlertTitle>Info</AlertTitle>
								<AlertDescription>Body copy for the alert.</AlertDescription>
							</div>
						</Alert>
					</div>
				</Row>
				<Row label="Stat">
					<Stat>
						<StatLabel>Runs</StatLabel>
						<StatValue>1,284</StatValue>
						<StatDelta direction="up">+ 12%</StatDelta>
					</Stat>
				</Row>

				<div className="mt-10">
					<a
						href="?story=index--landing"
						className="inline-flex items-center gap-1 text-sm text-accent hover:underline"
					>
						Back to landing
						<ArrowRight className="size-3.5" />
					</a>
				</div>
			</div>
	),
};

const meta: Meta = {
	title: "UI/_All",
};

export default meta;
