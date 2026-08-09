'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import s from './CommandLine.module.css';

interface Props {
  /** One command, or a list of commands to render as separate prompt lines.
   *  Copy button copies them joined by newlines. */
  command: string | string[];
  /** Optional prompt glyph. Default `$`. Pass empty string to hide. */
  prompt?: string;
  /** Optional aria label; defaults to `Copy command`. */
  ariaLabel?: string;
  className?: string;
}

/**
 * CommandLine — compact shell snippet with a single inline copy button.
 * Accepts one command or an array of commands (each rendered on its own
 * prompt line). Purpose-built for one-liner install / run commands.
 */
export function CommandLine({ command, prompt = '$', ariaLabel, className }: Props) {
  const [copied, setCopied] = useState(false);
  const lines = Array.isArray(command) ? command : [command];
  const raw = lines.join('\n');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(raw);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard blocked — silent no-op */
    }
  };

  const cls = [s.root, className].filter(Boolean).join(' ');

  return (
    <div className={cls} role="figure" aria-label={ariaLabel ?? 'shell command'}>
      <div className={s.body}>
        <button
          type="button"
          className={s.copy}
          onClick={handleCopy}
          aria-label={copied ? 'commands copied' : (ariaLabel ?? 'copy commands')}
        >
          {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
        </button>
        <div className={s.lines}>
          {lines.map((line, i) => (
            <div key={i} className={s.line}>
              {prompt && <span className={s.prompt} aria-hidden>{prompt}</span>}
              <code className={s.code}>{line}</code>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
