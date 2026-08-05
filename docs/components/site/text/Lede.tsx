import type { ReactNode } from 'react';
import s from './Lede.module.css';

interface Props {
  className?: string;
  children: ReactNode;
}

/** Lede — oversized intro paragraph. Zero margin. */
export function Lede({ className, children }: Props) {
  const cls = [s.lede, className].filter(Boolean).join(' ');
  return <p className={cls}>{children}</p>;
}
