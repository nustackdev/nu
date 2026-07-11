import Link from 'next/link';
import { NustackMark } from '@/components/marks/NustackMark';
import s from './Footer.module.css';

/**
 * Footer — three equal columns closing the page.
 */
export function Footer() {
  return (
    <footer className={s.footer} data-hue="s4">
      <div className={s.footerCell}>
        <span className={s.footerCellHead}>org</span>
        <span className={s.footerBrand}>
          <NustackMark />
        </span>
        <span className={s.footerCellBody}>
          <NustackMark /> © 2026
        </span>
      </div>
      <div className={s.footerCell}>
        <span className={s.footerCellHead}>explore</span>
        <span className={s.footerCellBody}>
          <a href="#interaction-model">the model</a>
        </span>
        <span className={s.footerCellBody}>
          <a href="#nu">Nu</a>
        </span>
        <span className={s.footerCellBody}>
          <a href="#apps">apps</a>
        </span>
      </div>
      <div className={s.footerCell}>
        <span className={s.footerCellHead}>elsewhere</span>
        <span className={s.footerCellBody}>
          <a href="https://github.com/nustackdev">github</a>
        </span>
        <span className={s.footerCellBody}>
          <Link href="/docs">docs</Link>
        </span>
      </div>
    </footer>
  );
}
