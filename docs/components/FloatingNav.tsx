'use client';

import Link from 'next/link';
import { Search, BookOpen } from 'lucide-react';
import { useSearchContext } from 'fumadocs-ui/contexts/search';
import { NuLogo } from '@/components/marks/NuLogo';
import { GithubMark } from '@/components/marks/GithubMark';
import s from './FloatingNav.module.css';

export function FloatingNav() {
  const { setOpenSearch } = useSearchContext();

  return (
    <header className={s.floatingNav}>
      <div className={s.navPill}>
        <Link href="/" className={s.navIcon} aria-label="nustack home">
          <NuLogo size={18} />
        </Link>

        <button
          type="button"
          className={s.navIcon}
          onClick={() => setOpenSearch(true)}
          aria-label="search"
        >
          <Search size={18} aria-hidden />
        </button>

        <Link href="/docs" className={s.navIcon} aria-label="docs">
          <BookOpen size={18} aria-hidden />
        </Link>

        <a
          className={s.navIcon}
          href="https://github.com/nustackdev/nu"
          target="_blank"
          rel="noreferrer"
          aria-label="github"
        >
          <GithubMark size={18} />
        </a>
      </div>
    </header>
  );
}
