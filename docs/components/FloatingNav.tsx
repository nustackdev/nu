'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search } from 'lucide-react';
import { useSearchContext } from 'fumadocs-ui/contexts/search';
import { NustackMark } from '@/components/marks/NustackMark';
import { NustackLogo } from '@/components/marks/NustackLogo';
import { GithubMark } from '@/components/marks/GithubMark';
import s from './FloatingNav.module.css';

export function FloatingNav() {
  const { setOpenSearch } = useSearchContext();
  const [isMac, setIsMac] = useState(true);

  useEffect(() => {
    setIsMac(/Mac|iPhone|iPad|iPod/.test(navigator.platform));
  }, []);

  return (
    <header className={s.floatingNav}>
      <div className={s.navPill}>
        <Link href="/" className={s.navBrand} aria-label="nustack home">
          <NustackLogo size={18} />
          <NustackMark />
        </Link>

        <span className={s.navDivider} aria-hidden />

        <nav className={s.navLinks}>
          <a href="#interaction-model">The model</a>
          <a href="#nu">Nu</a>
          <a href="#apps">Apps</a>
          <Link href="/docs">Docs</Link>
        </nav>

        <div className={s.navRight}>
          <button
            type="button"
            className={s.navSearch}
            onClick={() => setOpenSearch(true)}
            aria-label="search"
          >
            <Search size={13} aria-hidden />
            <span className={s.navSearchLabel}>Search</span>
            <span className={s.navSearchKbd} aria-hidden>
              <kbd>{isMac ? '⌘' : 'Ctrl'}</kbd>
              <kbd>K</kbd>
            </span>
          </button>

          <a
            className={s.navGithub}
            href="https://github.com/nustackdev"
            target="_blank"
            rel="noreferrer"
            aria-label="github"
          >
            <GithubMark size={16} />
          </a>
        </div>
      </div>
    </header>
  );
}
