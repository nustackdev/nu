import type { ReactNode } from 'react';
import s from './PageHero.module.css';

export interface PageHeroProps {
  children?: ReactNode;
  className?: string;
}

/**
 * PageHero — semantic wrapper for the top-of-page hero slot. Renders a
 * plain block; the hero's actual layout (Row/Cell/typography) lives inside.
 */
export function PageHero({ children, className }: PageHeroProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return <div className={cls}>{children}</div>;
}
