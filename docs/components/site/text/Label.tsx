import type { ReactNode } from 'react';
import s from './Label.module.css';

interface Props {
  className?: string;
  children: ReactNode;
}

/** Label — meta row / backend / status line. Zero margin. */
export function Label({ className, children }: Props) {
  const cls = [s.label, className].filter(Boolean).join(' ');
  return <p className={cls}>{children}</p>;
}
