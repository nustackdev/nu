import type { ReactNode } from 'react';
import { Cell } from '@/components/site/grid/Cell';
import { CellContent } from '@/components/site/grid/CellContent';
import { Row } from '@/components/site/grid/Row';
import type { RowStackAt } from '@/components/site/grid/Row';
import type { CellPad } from '@/components/site/grid/CellContent';
import s from './Section.module.css';

export type SectionHue = 'steel' | 'sage' | 'teal' | 'plum' | 'amber' | 'code';

/**
 * Split presets — each maps to a Row `cols` preset or a raw
 * `grid-template-columns` template. Unknown strings pass through as raw
 * templates so callers can drop in one-off proportions if needed.
 */
export type SectionSplit =
  | '1/1'
  | '1/2'
  | '2/1'
  | '45/55'
  | '55/45'
  | '1/1/1'
  | (string & {});

const HUE_CLASS: Record<SectionHue, string> = {
  steel: s.hueSteel,
  sage: s.hueSage,
  teal: s.hueTeal,
  plum: s.huePlum,
  amber: s.hueAmber,
  code: s.hueCode,
};

/**
 * Map a split token to a Row template string. Returns null when the token
 * matches a Row `cols` preset, so the caller can use the preset directly.
 */
function resolveSplit(split: SectionSplit): { cols?: 1 | 2 | 3 | '2:1' | '1:2'; template?: string } {
  switch (split) {
    case '1/1': return { cols: 2 };
    case '1/1/1': return { cols: 3 };
    case '1/2': return { cols: '1:2' };
    case '2/1': return { cols: '2:1' };
    case '45/55': return { template: 'minmax(0, 45fr) minmax(0, 55fr)' };
    case '55/45': return { template: 'minmax(0, 55fr) minmax(0, 45fr)' };
    default: return { template: split };
  }
}

export interface SectionProps {
  children?: ReactNode;
  /**
   * Column layout for this section. If provided, children are expected to
   * be `<SectionCell>`s (one per column). If omitted, the section is a
   * single column and children are auto-wrapped in a Cell + CellContent.
   */
  split?: SectionSplit;
  /** Accent hue scope applied to the whole section. */
  hue?: SectionHue;
  /**
   * Collapse this section to a single column at the given breakpoint.
   * Defaults to `sm` to match the site's global collapse behavior for
   * multi-column sections. Only meaningful when `split` is set.
   */
  stackAt?: RowStackAt;
  /** Padding for the auto-wrapped Cell when `split` is not provided. */
  pad?: CellPad;
  className?: string;
}

/**
 * Section — one bordered horizontal band in a page body. Bakes in the
 * standard `borderBottom borderLeft borderRight` story so sections stack
 * cleanly by default (each section's top border is implied by the previous
 * section's bottom border, and the last section closes the stack).
 *
 * With `split`, renders as a multi-column row; children should be
 * `<SectionCell>`s. Without `split`, renders as a single-column row and
 * auto-wraps children in Cell + CellContent for convenience.
 */
export function Section({
  children,
  split,
  hue,
  stackAt,
  pad = 'lg',
  className,
}: SectionProps) {
  const hueCls = hue ? HUE_CLASS[hue] : undefined;
  const cls = [hueCls, className].filter(Boolean).join(' ') || undefined;

  if (!split) {
    return (
      <Row cols={1} className={cls}>
        <Cell>
          <CellContent pad={pad}>{children}</CellContent>
        </Cell>
      </Row>
    );
  }

  const { cols, template } = resolveSplit(split);
  return (
    <Row
      cols={cols}
      template={template}
      stackAt={stackAt ?? 'sm'}
      className={cls}
    >
      {children}
    </Row>
  );
}
