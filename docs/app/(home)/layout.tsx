import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { baseOptions } from '@/lib/layout.shared';
import { FloatingNav } from '@/components/site/FloatingNav';

export default function Layout({ children }: LayoutProps<'/'>) {
  // Site is dark-only. Scoping `.dark` here forces fumadocs' CSS vars
  // (page bg, nav, borders) to their dark values on all (home) routes,
  // independent of the user's theme choice in /docs.
  return (
    <div className="dark">
      <HomeLayout {...baseOptions()} slots={{ header: FloatingNav }}>
        {children}
      </HomeLayout>
    </div>
  );
}
