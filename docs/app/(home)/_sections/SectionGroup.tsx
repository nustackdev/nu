import type { ReactNode } from 'react';
import s from './SectionGroup.module.css';

/**
 * SectionGroup — wraps a SectionCard with a giant ghost-silver "chapter"
 * label. The label sits pixel-perfectly above the card, its bottom edge
 * touching the card top. Geometry is driven by a single `--label-fs`
 * variable — see SectionGroup.module.css for the full explanation.
 *
 * Use at the page level:
 *   <SectionGroup label="theory"><InteractionModelSection /></SectionGroup>
 */
export function SectionGroup({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className={s.group}>
      <div className={s.labelBox} aria-hidden>
        <span className={s.label}>{label}</span>
      </div>
      {children}
    </div>
  );
}
