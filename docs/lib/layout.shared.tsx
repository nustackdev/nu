import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { NustackMark } from '@/components/site/marks/NustackMark';
import { gitConfig } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: <NustackMark />,
    },
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}
