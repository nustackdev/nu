// Layout node types: Sections that wrap other nodes.

import type { NodeEntry } from "../../tree";
import { Accordion } from "./accordion";
import { Card } from "./card";
import { Column } from "./column";
import { Container } from "./container";
import { Field } from "./field";
import { Fieldset } from "./fieldset";
import { Form } from "./form";
import { Modal } from "./modal";
import { Row } from "./row";
import { Tabs } from "./tabs";

export const layoutEntries: Record<string, NodeEntry> = {
	Column,
	Row,
	Container,
	Form,
	Fieldset,
	Field,
	Card,
	Tabs,
	Accordion,
	Modal,
};
