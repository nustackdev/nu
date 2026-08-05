import type { CSSProperties, ReactNode } from 'react';
import s from './Container.module.css';

export interface ContainerProps {
  children?: ReactNode;
  /** Max content width (px). Default 1360. */
  maxWidth?: number;
  /** If true, min-height: 100vh. */
  full?: boolean;
  className?: string;
  style?: CSSProperties;
}

/**
 * Container — outer wrapper for a site page.
 * Owns the layout tokens (--site-kal-u, --site-kal-border, --site-kal-divider) that all
 * descendants read.
 */
export function Container({
  children,
  maxWidth = 1360,
  full = false,
  className,
  style,
}: ContainerProps) {
  const cls = [s.root, full ? s.full : null, className].filter(Boolean).join(' ');
  return (
    <div
      className={cls}
      style={{ ['--site-kal-max-width' as string]: `${maxWidth}px`, ...style }}
    >
      {children}
    </div>
  );
}
