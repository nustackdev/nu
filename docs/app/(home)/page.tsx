import { Backdrop } from './_shell/Backdrop';
import { Hero } from './_hero/Hero';
import { HeroViz } from './_hero/HeroViz';
import { SectionGroup } from './_sections/SectionGroup';
import { InteractionModelSection } from './_sections/InteractionModelSection';
import { NuSection } from './_sections/NuSection';
import { FabricsSection } from './_sections/FabricsSection';
import { AppsSection } from './_sections/AppsSection';
import { Footer } from './_footer/Footer';

export default function HomePage() {
  return (
    <Backdrop>
      <Hero />
      <HeroViz />
      <SectionGroup label="theory">
        <InteractionModelSection />
      </SectionGroup>
      <SectionGroup label="nu">
        <NuSection />
      </SectionGroup>
      <SectionGroup label="fabrics">
        <FabricsSection />
      </SectionGroup>
      <SectionGroup label="apps">
        <AppsSection />
      </SectionGroup>
      <Footer />
    </Backdrop>
  );
}
