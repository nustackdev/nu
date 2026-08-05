import type { ReactNode } from 'react';
import s from './Chip.module.css';

export type ChipHue = 'steel' | 'sage' | 'teal' | 'plum' | 'amber';

interface Props {
  size: 'sm' | 'md';
  /** Optional hue tag — surfaced as a data-attr for parent-scope styling.
   *  The chip itself reads `--chip-hue / --chip-wash / --chip-line` (falling
   *  back to `--site-accent-2*`), which parent rows/containers already set. */
  hue?: ChipHue;
  className?: string;
  children: ReactNode;
}

/** Chip — small pill label. Hue routing is done by the surrounding scope. */
export function Chip({ size, hue, className, children }: Props) {
  const base = size === 'sm' ? s.sm : s.md;
  const cls = [base, className].filter(Boolean).join(' ');
  return (
    <span className={cls} data-hue={hue}>
      {children}
    </span>
  );
}
