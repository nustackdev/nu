import type { ReactNode } from 'react';
import s from './Page.module.css';

export interface PageProps {
  children?: ReactNode;
  className?: string;
}

/**
 * Page — content container inside PageShell. Owns the top margin that
 * clears the floating fixed nav so hero/body content doesn't collide with
 * it. Wraps PageHero + PageBody + PageFooter.
 */
export function Page({ children, className }: PageProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return <div className={cls}>{children}</div>;
}
