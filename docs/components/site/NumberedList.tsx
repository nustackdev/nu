import type { ReactNode } from 'react';
import s from './NumberedList.module.css';

interface Props {
  items: ReactNode[];
  className?: string;
}

/** NumberedList — mono-indexed vertical list (01, 02, …). */
export function NumberedList({ items, className }: Props) {
  const cls = [s.list, className].filter(Boolean).join(' ');
  return (
    <ol className={cls}>
      {items.map((label, i) => (
        <li key={i} className={s.item}>
          <span className={s.num}>{String(i + 1).padStart(2, '0')}</span>
          <span>{label}</span>
        </li>
      ))}
    </ol>
  );
}
