import { Backdrop } from './_shell/Backdrop';
import { Hero } from './_hero/Hero';
import { InteractionModelSection } from './_sections/InteractionModelSection';
import { NuSection } from './_sections/NuSection';
import { AppsSection } from './_sections/AppsSection';
import { Footer } from './_footer/Footer';

export default function HomePage() {
  return (
    <Backdrop>
      <Hero />
      <InteractionModelSection />
      <NuSection />
      <AppsSection />
      <Footer />
    </Backdrop>
  );
}
