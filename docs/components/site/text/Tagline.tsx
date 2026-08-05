import type { ReactNode } from 'react';
import s from './Tagline.module.css';

interface Props {
  className?: string;
  children: ReactNode;
}

/** Tagline — short accent phrase above a description. Zero margin. */
export function Tagline({ className, children }: Props) {
  const cls = [s.tagline, className].filter(Boolean).join(' ');
  return <p className={cls}>{children}</p>;
}
