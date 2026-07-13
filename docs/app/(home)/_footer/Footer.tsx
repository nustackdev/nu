import Link from 'next/link';
import { NustackMark } from '@/components/marks/NustackMark';
import s from './Footer.module.css';

/**
 * Footer — one simple row closing the page.
 */
export function Footer() {
  return (
    <footer className={s.footer} data-hue="s4">
      <Link href="/docs">Docs</Link>
      <span className={s.footerSep}>·</span>
      <a href="https://github.com/nustackdev">GitHub</a>
      <span className={s.footerSep}>·</span>
      <span className={s.footerBrand}>
        <NustackMark className={s.footerBrandMark} /> © 2026
      </span>
    </footer>
  );
}
