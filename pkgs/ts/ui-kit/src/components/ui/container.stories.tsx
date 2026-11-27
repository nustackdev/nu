import type { Meta, StoryObj } from "@storybook/react-vite";
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { Container } from "./container";
import { Text } from "./text";

/**
 * The page frame on a sunken page: the side gutter is the band between the
 * page edge and the card. It steps with the width the frame sits in (16 /
 * 32 / 48px), so a phone and a narrow column both get 16px.
 */
export const Default: StoryObj = {
	render: () => (
		<div className="bg-bg-sunken py-8">
			<Container className="gap-4">
				<Card>
					<CardHeader>
						<CardTitle>Frame</CardTitle>
					</CardHeader>
					<CardContent className="pb-4">
						<Text tone="secondary">Full width up to the main cap, centred.</Text>
					</CardContent>
				</Card>
			</Container>
		</div>
	),
};

const meta: Meta = {
	title: "UI/Container",
};

export default meta;
