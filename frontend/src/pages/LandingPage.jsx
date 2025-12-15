import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, MapPin, MessageCircle, Shield, Sparkles, ArrowRight, Users, Coins } from 'lucide-react';
import CustomCursor from '@/components/CustomCursor';
import AuthModal from '@/components/AuthModal';

gsap.registerPlugin(ScrollTrigger);

const LandingPage = () => {
  const [authModal, setAuthModal] = useState({ open: false, mode: 'login' });
  const heroRef = useRef(null);
  const featuresRef = useRef(null);

  const openLogin = () => setAuthModal({ open: true, mode: 'login' });
  const openSignup = () => setAuthModal({ open: true, mode: 'signup' });
  const closeModal = () => setAuthModal({ open: false, mode: 'login' });

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Hero animations
      gsap.from('.hero-title', {
        y: 60,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        delay: 0.3,
      });

      gsap.from('.hero-subtitle', {
        y: 40,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        delay: 0.5,
      });

      gsap.from('.hero-cta', {
        y: 30,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
        delay: 0.7,
      });

      gsap.from('.hero-image', {
        scale: 0.9,
        opacity: 0,
        duration: 1.2,
        ease: 'power3.out',
        delay: 0.4,
      });

      // Feature cards
      gsap.from('.feature-card', {
        y: 60,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: featuresRef.current,
          start: 'top 80%',
        },
      });

      // How it works
      gsap.from('.step-card', {
        x: -50,
        opacity: 0,
        duration: 0.8,
        stagger: 0.2,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: '.steps-section',
          start: 'top 75%',
        },
      });
    });

    return () => ctx.revert();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-purple-50/30 to-pink-50/30">
      <CustomCursor />

      {/* Floating shapes */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="floating-shape floating-shape-1" />
        <div className="floating-shape floating-shape-2" />
        <div className="floating-shape floating-shape-3" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-gray-900">TrueBond</span>
          </div>
          <div className="flex gap-3">
            <button onClick={openLogin} className="btn-ghost text-sm py-2.5 px-5">
              Login
            </button>
            <button onClick={openSignup} className="btn-primary text-sm py-2.5 px-5">
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section ref={heroRef} className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full mb-6">
                <Sparkles size={16} className="text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Find your perfect match</span>
              </div>

              <h1 className="hero-title text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
                Real connections
                <br />
                <span className="gradient-text">start here</span>
              </h1>

              <p className="hero-subtitle text-xl text-gray-600 mb-10 max-w-lg">
                Discover people nearby, spark meaningful conversations, and build authentic relationships that last.
              </p>

              <div className="flex flex-wrap gap-4 hero-cta">
                <button onClick={openSignup} className="btn-primary text-lg px-8 py-4 flex items-center gap-2">
                  Start Free <ArrowRight size={20} />
                </button>
                <button onClick={openLogin} className="btn-secondary text-lg px-8 py-4">
                  I have an account
                </button>
              </div>

              <div className="flex items-center gap-8 mt-12">
                {[
                  { value: '10', label: 'Free coins' },
                  { value: '50km', label: 'Discovery range' },
                  { value: '100%', label: 'Privacy' },
                ].map((stat, i) => (
                  <div key={i} className="hero-cta">
                    <div className="text-2xl font-bold text-purple-600">{stat.value}</div>
                    <div className="text-sm text-gray-500">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Hero Image/Illustration */}
            <div className="hero-image relative">
              <div className="relative w-full max-w-md mx-auto">
                {/* Phone mockup */}
                <div className="bg-white rounded-[3rem] p-3 shadow-2xl shadow-purple-200/50">
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-[2.5rem] p-6 aspect-[9/16] relative overflow-hidden">
                    {/* App preview content */}
                    <div className="space-y-4">
                      <div className="flex gap-3">
                        {[1, 2, 3, 4].map((i) => (
                          <div key={i} className="story-bubble">
                            <div className="story-bubble-inner bg-gradient-to-br from-purple-200 to-pink-200" />
                          </div>
                        ))}
                      </div>
                      {[1, 2].map((i) => (
                        <div key={i} className="bg-white rounded-2xl p-4 shadow-lg">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400" />
                            <div>
                              <div className="h-3 w-24 bg-gray-200 rounded" />
                              <div className="h-2 w-16 bg-gray-100 rounded mt-2" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Floating badges */}
                <div className="absolute -left-8 top-1/4 bg-white rounded-2xl p-4 shadow-xl animate-float">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <Users size={20} className="text-green-600" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold">5 nearby</div>
                      <div className="text-xs text-gray-500">Looking for you</div>
                    </div>
                  </div>
                </div>

                <div className="absolute -right-8 bottom-1/3 bg-white rounded-2xl p-4 shadow-xl animate-float" style={{ animationDelay: '-2s' }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                      <Heart size={20} className="text-purple-600" fill="currentColor" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold">New match!</div>
                      <div className="text-xs text-gray-500">Say hello 👋</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Why choose <span className="gradient-text">TrueBond</span>
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to find meaningful connections
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: MapPin, title: 'Live Location', desc: 'Find people near you in real-time', color: 'from-blue-500 to-cyan-500' },
              { icon: MessageCircle, title: 'Smart Chat', desc: 'Connect with 1 coin per message', color: 'from-purple-500 to-pink-500' },
              { icon: Shield, title: 'Privacy First', desc: 'Your address stays private always', color: 'from-green-500 to-emerald-500' },
              { icon: Coins, title: 'Fair Pricing', desc: 'Start with 10 free coins', color: 'from-amber-500 to-orange-500' },
            ].map((feature, i) => (
              <div key={i} className="feature-card card text-center">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mx-auto mb-4`}>
                  <feature.icon size={28} className="text-white" />
                </div>
                <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="steps-section py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Get started in <span className="gradient-text">3 steps</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { num: '01', title: 'Create Profile', desc: 'Sign up and add your photos. Tell us about yourself.' },
              { num: '02', title: 'Discover Nearby', desc: 'Find interesting people around you on the map.' },
              { num: '03', title: 'Start Chatting', desc: 'Send a message and start your journey together.' },
            ].map((step, i) => (
              <div key={i} className="step-card relative">
                <div className="text-7xl font-bold text-purple-100 mb-4">{step.num}</div>
                <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                <p className="text-gray-600">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-3xl p-12 text-white">
            <Heart size={48} className="mx-auto mb-6" fill="white" />
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Ready to find your bond?</h2>
            <p className="text-xl text-white/90 mb-8 max-w-xl mx-auto">
              Join thousands finding meaningful connections every day.
            </p>
            <button onClick={openSignup} className="bg-white text-purple-600 font-bold px-10 py-4 rounded-full hover:shadow-xl transition-all">
              Get Started Free
            </button>
            <p className="text-white/70 text-sm mt-4">10 free coins • No credit card required</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Heart size={16} className="text-white" fill="white" />
            </div>
            <span className="font-bold text-gray-900">TrueBond</span>
          </div>
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} TrueBond. All rights reserved.
          </p>
        </div>
      </footer>

      <AuthModal isOpen={authModal.open} onClose={closeModal} initialMode={authModal.mode} />
    </div>
  );
};

export default LandingPage;
