import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import CustomCursor from '../components/CustomCursor';
import AuthModal from '../components/AuthModal';
import HeroSection from '../components/landing/HeroSection';
import HowItWorksSection from '../components/landing/HowItWorksSection';
import LocationSection from '../components/landing/LocationSection';
import CreditsSection from '../components/landing/CreditsSection';
import PrivacySection from '../components/landing/PrivacySection';
import CTASection from '../components/landing/CTASection';

gsap.registerPlugin(ScrollTrigger);

const LandingPage = () => {
  const [authModal, setAuthModal] = useState({ open: false, mode: 'login' });
  const containerRef = useRef(null);

  const openLogin = () => setAuthModal({ open: true, mode: 'login' });
  const openSignup = () => setAuthModal({ open: true, mode: 'signup' });
  const closeModal = () => setAuthModal({ open: false, mode: 'login' });

  useEffect(() => {
    // Smooth scroll setup
    const ctx = gsap.context(() => {
      // Parallax background elements
      gsap.utils.toArray('.parallax-bg').forEach((el) => {
        gsap.to(el, {
          yPercent: -30,
          ease: 'none',
          scrollTrigger: {
            trigger: el.parentElement,
            start: 'top bottom',
            end: 'bottom top',
            scrub: true,
          },
        });
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="bg-[#0B0B0F] min-h-screen">
      <CustomCursor />
      <div className="noise-overlay" />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="text-2xl font-bold gradient-text">TrueBond</div>
          <div className="flex gap-4">
            <button onClick={openLogin} className="btn-secondary text-sm py-3 px-6">
              Login
            </button>
            <button onClick={openSignup} className="btn-primary text-sm py-3 px-6">
              Join Now
            </button>
          </div>
        </div>
      </nav>

      {/* Sections */}
      <HeroSection onJoinClick={openSignup} onLoginClick={openLogin} />
      <HowItWorksSection />
      <LocationSection />
      <CreditsSection />
      <PrivacySection />
      <CTASection onJoinClick={openSignup} />

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto text-center">
          <div className="text-2xl font-bold gradient-text mb-4">TrueBond</div>
          <p className="text-white/40 text-sm">
            © {new Date().getFullYear()} TrueBond. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModal.open}
        onClose={closeModal}
        initialMode={authModal.mode}
      />
    </div>
  );
};

export default LandingPage;
