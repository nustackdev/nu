import type { CSSProperties, ReactNode } from 'react';
import s from './Cell.module.css';

export interface CellProps {
  children?: ReactNode;
  /** How many template columns this cell spans. Default 1. */
  span?: number;
  className?: string;
  style?: CSSProperties;
}

/** Cell — grid item inside a Row. No padding; wrap content in CellContent. */
export function Cell({ children, span = 1, className, style }: CellProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return (
    <div
      className={cls}
      style={{ ['--kal-cell-span' as string]: String(span), ...style }}
    >
      {children}
    </div>
  );
}
