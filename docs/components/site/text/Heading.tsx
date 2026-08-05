import type { ReactNode } from 'react';
import s from './Heading.module.css';

interface Props {
  level: 1 | 2;
  className?: string;
  children: ReactNode;
}

/** Heading — level=1 renders <h2> (section title), level=2 renders <h3>
 *  (subsection title). Emits zero margin; parent owns rhythm. */
export function Heading({ level, className, children }: Props) {
  const cls = [level === 1 ? s.h1 : s.h2, className].filter(Boolean).join(' ');
  if (level === 1) return <h2 className={cls}>{children}</h2>;
  return <h3 className={cls}>{children}</h3>;
}
