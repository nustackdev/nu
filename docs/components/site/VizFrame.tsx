import type { ReactNode } from 'react';
import s from './VizFrame.module.css';

export type VizFrameHue = 'steel' | 'sage' | 'teal' | 'plum' | 'amber';

interface Props {
  children: ReactNode;
  /** `solid` (default) — sits on a solid section card, subtle white wash.
   *  `glass`           — sits on a translucent glass card, darker inner bg. */
  surface?: 'solid' | 'glass';
  /** Remaps --nu-accent[-2] to a silver-woven fabric hue so any shared SVG
   *  primitive inside (BrowserChrome, DiskStack, …) auto-tints. */
  hue?: VizFrameHue;
  className?: string;
}

/** VizFrame — bordered dot-grid canvas for viz SVGs. */
export function VizFrame({ children, surface = 'solid', hue, className }: Props) {
  const base = surface === 'glass' ? s.glass : s.solid;
  const cls = [base, className].filter(Boolean).join(' ');
  return (
    <div className={cls} data-hue={hue}>
      {children}
    </div>
  );
}
