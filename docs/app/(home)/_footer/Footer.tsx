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
        <span className={s.footerCellHead}>Org</span>
        <span className={s.footerBrand}>
          <NustackMark />
        </span>
        <span className={s.footerCellBody}>
          <NustackMark /> © 2026
        </span>
      </div>
      <div className={s.footerCell}>
        <span className={s.footerCellHead}>Explore</span>
        <span className={s.footerCellBody}>
          <a href="#interaction-model">The model</a>
        </span>
        <span className={s.footerCellBody}>
          <a href="#nu">Nu</a>
        </span>
        <span className={s.footerCellBody}>
          <a href="#apps">Apps</a>
        </span>
      </div>
      <div className={s.footerCell}>
        <span className={s.footerCellHead}>Elsewhere</span>
        <span className={s.footerCellBody}>
          <a href="https://github.com/nustackdev">GitHub</a>
        </span>
        <span className={s.footerCellBody}>
          <Link href="/docs">Docs</Link>
        </span>
      </div>
    </footer>
  );
}
