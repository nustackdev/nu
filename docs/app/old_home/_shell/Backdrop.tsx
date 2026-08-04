import type { ReactNode } from 'react';
import s from './Backdrop.module.css';

/**
 * Backdrop — outer page wrapper.
 * Paints the JB gradient + dot grain, and hosts the shell column that all
 * page sections stack inside.
 */
export function Backdrop({ children }: { children: ReactNode }) {
  return (
    <div className={s.root}>
      <div className={s.heroBg} aria-hidden />
      <div className={s.pageBg} aria-hidden />
      <div className={s.grain} aria-hidden />
      <div className={s.shell}>{children}</div>
    </div>
  );
}
