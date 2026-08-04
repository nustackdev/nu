import type { CSSProperties } from 'react';
import s from './DotPattern.module.css';

export interface DotPatternProps {
  /** Fixed (viewport) vs absolute (scoped to positioned parent). Default true. */
  fixed?: boolean;
  /** Layer opacity. Default 0.35 (matches live shell). */
  opacity?: number;
  className?: string;
  style?: CSSProperties;
}

/** DotPattern — the dense dot tooth from the live landing, as a drop-in layer. */
export function DotPattern({
  fixed = true,
  opacity = 0.35,
  className,
  style,
}: DotPatternProps) {
  const cls = [s.root, fixed ? s.fixed : s.absolute, className]
    .filter(Boolean)
    .join(' ');
  return (
    <div
      aria-hidden
      className={cls}
      style={{ ['--kal-dot-opacity' as string]: String(opacity), ...style }}
    />
  );
}
