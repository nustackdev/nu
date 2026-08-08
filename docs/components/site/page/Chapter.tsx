import type { ReactNode } from 'react';
import s from './Chapter.module.css';

export interface ChapterProps {
  children?: ReactNode;
  className?: string;
}

/**
 * Chapter — one grouping card inside PageBody. Wraps a SectionHead plus
 * its Sections into a single visual object (border, radius, dimmed bg,
 * unified line weights). Multiple Chapters stack inside PageBody separated
 * by vertical gap.
 */
export function Chapter({ children, className }: ChapterProps) {
  const cls = [s.root, className].filter(Boolean).join(' ');
  return <div className={cls}>{children}</div>;
}
