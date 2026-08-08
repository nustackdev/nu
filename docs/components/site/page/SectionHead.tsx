import type { ReactNode } from 'react';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Row } from '@/components/site/grid/Row';
import { Heading } from '@/components/site/text';
import s from './SectionHead.module.css';

export interface SectionHeadProps {
  /** Head title, rendered as a Heading. */
  title: ReactNode;
  /** Optional lede paragraph shown under the title. */
  lede?: ReactNode;
  /** Heading level. Default 1. */
  level?: 1 | 2;
  className?: string;
}

/**
 * SectionHead — chapter title row: heading with an optional lede beneath.
 * Peek watermark removed (was noise).
 */
export function SectionHead({
  title,
  lede,
  level = 1,
  className,
}: SectionHeadProps) {
  return (
    <Row cols={1} className={className}>
      <Cell>
        <CellContent pad="lg">
          <Heading level={level}>{title}</Heading>
          {lede ? <p className={s.lede}>{lede}</p> : null}
        </CellContent>
      </Cell>
    </Row>
  );
}
