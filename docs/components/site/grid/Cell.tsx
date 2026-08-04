import type { CSSProperties, ReactNode } from 'react';
import s from './Cell.module.css';

export type CellXAlign = 'left' | 'center' | 'right';
export type CellYAlign = 'top' | 'middle' | 'bottom';

export interface CellProps {
  children?: ReactNode;
  /** How many template columns this cell spans. Default 1. */
  span?: number;
  /** Horizontal alignment of the cell's content. Default 'left'. */
  xalign?: CellXAlign;
  /** Vertical alignment of the cell's content. Default 'top'. */
  yalign?: CellYAlign;
  className?: string;
  style?: CSSProperties;
}

/** Cell — grid item inside a Row. No padding; wrap content in CellContent. */
export function Cell({
  children,
  span = 1,
  xalign = 'left',
  yalign = 'top',
  className,
  style,
}: CellProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return (
    <div
      className={cls}
      data-xalign={xalign}
      data-yalign={yalign}
      style={{ ['--kal-cell-span' as string]: String(span), ...style }}
    >
      {children}
    </div>
  );
}
