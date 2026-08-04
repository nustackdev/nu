import type { CSSProperties, ReactNode } from 'react';
import s from './Row.module.css';

export type RowCols = 1 | 2 | 3 | '2:1' | '1:2';
export type RowBorder = false | 'solid' | 'dashed' | 'dotted';

export interface RowProps {
  children?: ReactNode;
  /** Preset column layout. Ignored if `template` is set. */
  cols?: RowCols;
  /** Escape hatch: raw grid-template-columns value. */
  template?: string;
  borderTop?: RowBorder;
  borderBottom?: RowBorder;
  borderLeft?: RowBorder;
  borderRight?: RowBorder;
  /** Vertical rule style between cells. Default 'dashed'. */
  divider?: RowBorder;
  className?: string;
  style?: CSSProperties;
}

const COL_TEMPLATES: Record<RowCols, string> = {
  1: 'minmax(0, 1fr)',
  2: 'minmax(0, 1fr) minmax(0, 1fr)',
  3: 'minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr)',
  '2:1': 'minmax(0, 2fr) minmax(0, 1fr)',
  '1:2': 'minmax(0, 1fr) minmax(0, 2fr)',
};

const SIDE_CLASS: Record<
  'bt' | 'bb' | 'bl' | 'br',
  Record<Exclude<RowBorder, false>, string>
> = {
  bt: { solid: s.btSolid, dashed: s.btDashed, dotted: s.btDotted },
  bb: { solid: s.bbSolid, dashed: s.bbDashed, dotted: s.bbDotted },
  bl: { solid: s.blSolid, dashed: s.blDashed, dotted: s.blDotted },
  br: { solid: s.brSolid, dashed: s.brDashed, dotted: s.brDotted },
};

const DIVIDER_CLASS: Record<Exclude<RowBorder, false>, string> = {
  solid: s.divSolid,
  dashed: s.divDashed,
  dotted: s.divDotted,
};

/**
 * Row — one horizontal band inside a Container. Lays out Cells in a grid
 * and handles outer borders + inter-cell dividers.
 */
export function Row({
  children,
  cols = 1,
  template,
  borderTop = false,
  borderBottom = false,
  borderLeft = false,
  borderRight = false,
  divider = 'dashed',
  className,
  style,
}: RowProps) {
  const gridTemplate = template ?? COL_TEMPLATES[cols];
  const cls = [
    s.root,
    borderTop && SIDE_CLASS.bt[borderTop],
    borderBottom && SIDE_CLASS.bb[borderBottom],
    borderLeft && SIDE_CLASS.bl[borderLeft],
    borderRight && SIDE_CLASS.br[borderRight],
    divider && DIVIDER_CLASS[divider],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={cls}
      style={{ ['--kal-row-template' as string]: gridTemplate, ...style }}
    >
      {children}
    </div>
  );
}
