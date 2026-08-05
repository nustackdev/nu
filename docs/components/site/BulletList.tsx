import type { ReactNode } from 'react';
import s from './BulletList.module.css';

interface Props {
  items: ReactNode[];
  className?: string;
}

/** BulletList — dash-bulleted vertical list. Mirrors NumberedList styling. */
export function BulletList({ items, className }: Props) {
  const cls = [s.list, className].filter(Boolean).join(' ');
  return (
    <ul className={cls}>
      {items.map((label, i) => (
        <li key={i} className={s.item}>
          <span className={s.bullet}>-</span>
          <span>{label}</span>
        </li>
      ))}
    </ul>
  );
}
