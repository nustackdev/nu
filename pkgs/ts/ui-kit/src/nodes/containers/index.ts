// Container node types: open-ended children, optional chrome of their own.
//
// The Python side mirrors it: one container Ref per type here (RowRef,
// CardRef, ...), with a Shape over each. Everything else the kit draws is a
// leaf and lives in the other groups.

import type { NodeEntry } from "../../tree";
import { Accordion } from "./accordion";
import { Card } from "./card";
import { Collapsible } from "./collapsible";
import { Column } from "./column";
import { Container } from "./container";
import { Field } from "./field";
import { Fieldset } from "./fieldset";
import { Form } from "./form";
import { Grid } from "./grid";
import { Line } from "./line";
import { ListRef } from "./list";
import { Modal } from "./modal";
import { Row } from "./row";
import { Sheet } from "./sheet";
import { Tabs } from "./tabs";

export const containerEntries: Record<string, NodeEntry> = {
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
	ListRef,
	Grid,
	Line,
	Collapsible,
	Sheet,
};
