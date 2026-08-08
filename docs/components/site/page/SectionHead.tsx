import type { ReactNode } from 'react';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Row } from '@/components/site/grid/Row';
import { Heading } from '@/components/site/text';
import s from './SectionHead.module.css';

export interface SectionHeadProps {
  /** Giant background watermark word ("intro", "fabrics", "apps"…). */
  peek?: string;
  /** Head title, rendered as a Heading. */
  title: ReactNode;
  /** Optional lede paragraph shown under the title. */
  lede?: ReactNode;
  /** Heading level. Default 1 (renders <h2> — see Heading). */
  level?: 1 | 2;
  className?: string;
}

/**
 * SectionHead — chapter header row. Bakes the peek watermark + Heading +
 * lede pattern that opens each landing chapter. Rendered as its own
 * bordered Row so it stacks flush with the Sections below.
 */
export function SectionHead({
  peek,
  title,
  lede,
  level = 1,
  className,
}: SectionHeadProps) {
  return (
    <Row cols={1} className={className}>
      <Cell className={s.headCell}>
        {peek ? <span className={s.peek} aria-hidden>{peek}</span> : null}
        <CellContent pad="lg">
          <Heading level={level}>{title}</Heading>
          {lede ? <p className={s.lede}>{lede}</p> : null}
        </CellContent>
      </Cell>
    </Row>
  );
}
