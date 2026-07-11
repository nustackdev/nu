import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { baseOptions } from '@/lib/layout.shared';
import { FloatingNav } from '@/components/FloatingNav';

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <HomeLayout {...baseOptions()} slots={{ header: FloatingNav }}>
      {children}
    </HomeLayout>
  );
}
