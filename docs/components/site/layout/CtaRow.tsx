import type { CSSProperties, ReactNode } from 'react';
import s from './CtaRow.module.css';

interface Props {
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}

/** CtaRow — non-hero CTA button row. Zero external margin; wrap in a
 *  <Stack> for rhythm. Hero uses a separate .heroCtaRow variant. */
export function CtaRow({ className, style, children }: Props) {
  const cls = [s.ctaRow, className].filter(Boolean).join(' ');
  return (
    <div className={cls} style={style}>
      {children}
    </div>
  );
}
