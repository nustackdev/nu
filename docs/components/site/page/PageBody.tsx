import type { ReactNode } from 'react';
import s from './PageBody.module.css';

export interface PageBodyProps {
  children?: ReactNode;
  className?: string;
}

/**
 * PageBody — semantic wrapper for the body vessel that hosts a stack of
 * `<Section>` / `<SectionHead>` calls. Border/card styling is deliberately
 * deferred; today it's just a hook.
 */
export function PageBody({ children, className }: PageBodyProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return <div className={cls}>{children}</div>;
}
