import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, Home, AlertTriangle, Lightbulb, Star, RotateCcw, Shield, CreditCard, HelpCircle, Rocket } from 'lucide-react';
import CustomCursor from '@/components/CustomCursor';
import AuthModal from '@/components/AuthModal';

// Landing sections
import Navigation from '@/components/landing/Navigation';
import HeroSection from '@/components/landing/HeroSection';
import ProblemSection from '@/components/landing/ProblemSection';
import PhilosophySection from '@/components/landing/PhilosophySection';
import FeaturesSection from '@/components/landing/FeaturesSection';
import HowItWorksSection from '@/components/landing/HowItWorksSection';
import SafetySection from '@/components/landing/SafetySection';
import PricingSection from '@/components/landing/PricingSection';
import SupportSection from '@/components/landing/SupportSection';
import CTASection from '@/components/landing/CTASection';
import FooterSection from '@/components/landing/FooterSection';

gsap.registerPlugin(ScrollTrigger);

const navItems = [
  { id: 'hero', icon: Home, label: 'Home' },
  { id: 'problem', icon: AlertTriangle, label: 'The Problem' },
  { id: 'philosophy', icon: Lightbulb, label: 'Our Philosophy' },
  { id: 'features', icon: Star, label: 'Features' },
  { id: 'how-it-works', icon: RotateCcw, label: 'How It Works' },
  { id: 'safety', icon: Shield, label: 'Safety' },
  { id: 'pricing', icon: CreditCard, label: 'Pricing' },
  { id: 'support', icon: HelpCircle, label: 'Support' },
  { id: 'cta', icon: Rocket, label: 'Get Started' },
];

const LandingPage = () => {
  const [activeSection, setActiveSection] = useState('hero');
  const [authModal, setAuthModal] = useState({ open: false, mode: 'login' });
  const containerRef = useRef(null);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleNavigate = (sectionId) => {
    scrollToSection(sectionId);
  };

  const handleGetStarted = () => {
    setAuthModal({ open: true, mode: 'signup' });
  };

  const handleWaitlist = () => {
    alert('Join our waitlist!\n\nEmail: waitlist@truebond.com\n\nIn production, this would open an email capture form.');
  };

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Hero animations
      gsap.from('.hero-badge', { y: -40, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.2 });
      gsap.from('.hero-title', { y: 60, opacity: 0, duration: 1.2, ease: 'power3.out', delay: 0.4 });
      gsap.from('.hero-subtitle', { y: 40, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.6 });
      gsap.from('.hero-cta', { y: 30, opacity: 0, duration: 0.8, stagger: 0.15, ease: 'power3.out', delay: 0.8 });

      // Active section detection
      navItems.forEach(({ id }) => {
        ScrollTrigger.create({
          trigger: `#${id}`,
          start: 'top center',
          end: 'bottom center',
          onEnter: () => setActiveSection(id),
          onEnterBack: () => setActiveSection(id),
        });
      });

      // Section reveal animations
      const sections = document.querySelectorAll('section[id]');
      sections.forEach((section) => {
        gsap.from(section.querySelectorAll('.section-reveal'), {
          scrollTrigger: {
            trigger: section,
            start: 'top 80%',
            toggleActions: 'play none none reverse',
          },
          y: 60,
          opacity: 0,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
        });
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="min-h-screen bg-[#F8FAFC]">
      <CustomCursor />

      {/* TOP HEADER - App Name Left, Auth Right */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* App Name - Left */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#0F172A] flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-[#0F172A]">TrueBond</span>
          </div>

          {/* Auth Buttons - Right */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAuthModal({ open: true, mode: 'login' })}
              className="px-5 py-2 text-gray-700 font-medium hover:text-[#0F172A] transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => setAuthModal({ open: true, mode: 'signup' })}
              className="px-5 py-2 bg-[#0F172A] text-white font-medium rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              Sign Up
            </button>
          </div>
        </div>
      </header>

      {/* LEFT DOT NAVIGATION */}
      <Navigation activeSection={activeSection} onNavigate={handleNavigate} />

      {/* MOBILE BOTTOM NAV */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-t border-gray-100 px-2 py-2 safe-area-pb">
        <div className="flex justify-around overflow-x-auto scrollbar-hide">
          {navItems.slice(0, 5).map((item) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className={`flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors ${
                activeSection === item.id ? 'text-rose-500' : 'text-gray-400'
              }`}
            >
              <item.icon size={20} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* ===== SECTIONS ===== */}
      <HeroSection onGetStarted={handleGetStarted} onWaitlist={handleWaitlist} />
      <ProblemSection />
      <PhilosophySection />
      <FeaturesSection />
      <HowItWorksSection />
      <SafetySection />
      <PricingSection onGetStarted={handleGetStarted} />
      <SupportSection />
      <CTASection onGetStarted={handleGetStarted} />
      <FooterSection />

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModal.open}
        onClose={() => setAuthModal({ open: false, mode: 'login' })}
        initialMode={authModal.mode}
      />
    </div>
  );
};

export default LandingPage;
