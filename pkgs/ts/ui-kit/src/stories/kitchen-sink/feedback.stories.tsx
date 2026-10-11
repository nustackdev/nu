// Kitchen sink: status, progress and empty states, light and dark side by side.
// Tooltip portals out of the dark column, so it lives on the Overlays page.

import type { Meta, StoryObj } from "@storybook/react-vite";
import { Inbox, Star } from "lucide-react";
import { Alert, AlertDescription, AlertIcon, AlertTitle } from "../../components/ui/alert";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { EmptyState } from "../../components/ui/empty-state";
import { Progress } from "../../components/ui/progress";
import { Skeleton } from "../../components/ui/skeleton";
import { Spinner } from "../../components/ui/spinner";
import { StatusDot } from "../../components/ui/status-dot";
import { StatusPill } from "../../components/ui/status-pill";
import { Text } from "../../components/ui/text";
import { Block, Row, SinkPage, ThemePair, sinkParameters } from "./frame";

const ALERT_TONES = ["neutral", "info", "ok", "warn", "danger"] as const;
const BADGE_VARIANTS = [
	"default",
	"secondary",
	"outline",
	"info",
	"ok",
	"warn",
	"danger",
	"dashed",
] as const;
const STATUS_TONES = ["neutral", "info", "ok", "warn", "danger"] as const;
const PROGRESS_TONES = ["default", "info", "ok", "warn", "danger"] as const;
const SPINNER_TONES = ["default", "neutral", "info", "ok", "warn", "danger"] as const;

function Status() {
	return (
		<Block title="Status">
			<Row label="Alert" className="flex-col items-stretch gap-2">
				{ALERT_TONES.map((tone) => (
					<Alert key={tone} tone={tone}>
						<AlertIcon />
						<div>
							<AlertTitle>Alert {tone}</AlertTitle>
							<AlertDescription>The plane restarted and picked up where it left off.</AlertDescription>
						</div>
					</Alert>
				))}
			</Row>
			{(["sm", "md", "lg"] as const).map((size) => (
				<Row key={size} label={`Badge ${size}`}>
					{BADGE_VARIANTS.map((variant) => (
						<Badge key={variant} variant={variant} size={size}>
							{variant}
						</Badge>
					))}
				</Row>
			))}
			<Row label="Badge icon">
				<Badge>
					<Star />
					starred
				</Badge>
				<Badge variant="ok">
					<Star />
					ok
				</Badge>
			</Row>
			{(["sm", "md"] as const).map((size) => (
				<Row key={size} label={`StatusPill ${size}`}>
					{STATUS_TONES.map((tone) => (
						<StatusPill key={tone} tone={tone} size={size}>
							{tone}
						</StatusPill>
					))}
				</Row>
			))}
			<Row label="StatusDot">
				{STATUS_TONES.map((tone) => (
					<span key={tone} className="flex items-center gap-1.5">
						<StatusDot tone={tone} />
						<Text as="span" size="sm" tone="secondary">
							{tone}
						</Text>
					</span>
				))}
				<span className="flex items-center gap-1.5">
					<StatusDot tone="info" pulse />
					<Text as="span" size="sm" tone="secondary">
						pulse
					</Text>
				</span>
			</Row>
		</Block>
	);
}

function Loading() {
	return (
		<Block title="Loading">
			<Row label="Progress" className="flex-col items-stretch gap-3">
				{PROGRESS_TONES.map((tone, i) => (
					<Progress key={tone} tone={tone} value={20 + i * 15} aria-label={tone} />
				))}
				<div className="flex items-center gap-3">
					<Progress size="sm" value={40} aria-label="sm" />
					<Progress size="lg" value={70} aria-label="lg" />
				</div>
			</Row>
			<Row label="Spinner">
				{(["sm", "md", "lg", "xl"] as const).map((size) => (
					<Spinner key={size} size={size} />
				))}
				{SPINNER_TONES.map((tone) => (
					<Spinner key={tone} tone={tone} />
				))}
				<Button size="sm" disabled>
					<Spinner tone="onSolid" size="sm" />
					Saving
				</Button>
			</Row>
			<Row label="Skeleton">
				<Skeleton shape="circle" className="size-8" />
				<div className="flex w-48 flex-col gap-1.5">
					<Skeleton shape="text" className="w-3/4" />
					<Skeleton shape="text" className="w-1/2" />
				</div>
				<Skeleton className="h-12 w-24" />
			</Row>
			<Row label="EmptyState">
				<EmptyState icon={<Inbox />} description="Create one to start." action={<Button size="sm">New plane</Button>}>
					No planes yet
				</EmptyState>
				<EmptyState size="sm" icon={<Spinner size="sm" />}>
					Loading runs
				</EmptyState>
			</Row>
			<Row label="Tooltip">
				<Text size="sm" tone="muted">
					Portals to the body: see Kitchen Sink / Overlays.
				</Text>
			</Row>
		</Block>
	);
}

export const Default: StoryObj = {
	name: "Feedback",
	render: () => (
		<SinkPage title="Feedback" description="Alerts, badges, status, progress and empty states.">
			<ThemePair>
				<Status />
				<Loading />
			</ThemePair>
		</SinkPage>
	),
};

const meta: Meta = {
	title: "Kitchen Sink/Feedback",
	parameters: sinkParameters,
};

export default meta;
