import type { ElementType, ReactNode } from 'react';
import s from './MonoKicker.module.css';

interface Props {
  size?: 'xs' | 'sm' | 'md';
  tracking?: 'wide' | 'wider';
  as?: ElementType;
  className?: string;
  children: ReactNode;
}

/** MonoKicker — the small uppercase-mono micro-label used for kickers,
 *  metadata strips, and colophon-style fine print. */
export function MonoKicker({
  size = 'xs',
  tracking = 'wide',
  as: Tag = 'span',
  className,
  children,
}: Props) {
  const sizeCls = size === 'xs' ? s.xs : size === 'sm' ? s.sm : s.md;
  const trackCls = tracking === 'wider' ? s.wider : s.wide;
  const cls = [sizeCls, trackCls, className].filter(Boolean).join(' ');
  return <Tag className={cls}>{children}</Tag>;
}
