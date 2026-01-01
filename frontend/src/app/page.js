import Image from "next/image";
import IntroSection from "../landing/IntroSection";
import Navbar from "../components/ui/Navbar";
import UserGuide from "../landing/UserGuide";

import AnimatedBackground from "../landing/AnimatedBackground";
import SearchPreview from "../landing/SearchPreview";
import DemoPlaceholder from "../landing/DemoPlaceholder";
import Footer from "../components/ui/Footer";
export default function Home() {
  return (
    <>
      
      <AnimatedBackground>
        <Navbar />
        <IntroSection />
        <UserGuide />
        <SearchPreview />
        <DemoPlaceholder />
        <Footer />
      </AnimatedBackground>

    </>
  );
}
