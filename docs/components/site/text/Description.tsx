import type { ReactNode } from 'react';
import s from './Description.module.css';

interface Props {
  className?: string;
  children: ReactNode;
}

/** Description — default body paragraph. Zero margin. */
export function Description({ className, children }: Props) {
  const cls = [s.description, className].filter(Boolean).join(' ');
  return <p className={cls}>{children}</p>;
}
