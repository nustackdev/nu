import type { CSSProperties, ReactNode } from 'react';
import s from './CellContent.module.css';

export type CellPad = 'none' | 'sm' | 'md' | 'lg';

export interface CellContentProps {
  children?: ReactNode;
  /** Padding scale in units of --kal-u. Default 'md'. */
  pad?: CellPad;
  className?: string;
  style?: CSSProperties;
}

/** CellContent — the padded box that lives inside a Cell. */
export function CellContent({
  children,
  pad = 'md',
  className,
  style,
}: CellContentProps) {
  const cls = [s[pad], className].filter(Boolean).join(' ');
  return (
    <div className={cls} style={style}>
      {children}
    </div>
  );
}
