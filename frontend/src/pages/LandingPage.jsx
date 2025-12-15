import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, MapPin, MessageCircle, Shield, Sparkles, ArrowRight, Users, Coins, Home, Star, Compass, Info, LogIn, UserPlus, ChevronLeft, ChevronRight } from 'lucide-react';
import CustomCursor from '@/components/CustomCursor';

gsap.registerPlugin(ScrollTrigger);

const LandingPage = () => {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const heroRef = useRef(null);
  const featuresRef = useRef(null);
  const nearbyRef = useRef(null);
  const howItWorksRef = useRef(null);

  useEffect(() => {
    // Handle scroll for nav collapse
    const handleScroll = () => {
      setNavCollapsed(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);

    const ctx = gsap.context(() => {
      // Hero animations
      gsap.from('.hero-badge', {
        y: -30,
        opacity: 0,
        duration: 0.8,
        ease: 'power3.out',
        delay: 0.2,
      });

      gsap.from('.hero-title', {
        y: 80,
        opacity: 0,
        duration: 1.2,
        ease: 'power3.out',
        delay: 0.4,
      });

      gsap.from('.hero-subtitle', {
        y: 50,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        delay: 0.6,
      });

      gsap.from('.hero-cta', {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
        delay: 0.8,
      });

      gsap.from('.hero-visual', {
        scale: 0.8,
        opacity: 0,
        duration: 1.4,
        ease: 'power3.out',
        delay: 0.5,
      });

      gsap.from('.floating-card', {
        y: 100,
        opacity: 0,
        duration: 1,
        stagger: 0.2,
        ease: 'power3.out',
        delay: 1,
      });

      // Floating animation loop
      gsap.to('.float-1', {
        y: -20,
        duration: 3,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      });

      gsap.to('.float-2', {
        y: -15,
        duration: 2.5,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: 0.5,
      });

      gsap.to('.float-3', {
        y: -25,
        duration: 3.5,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
        delay: 1,
      });

      // Background blobs animation
      gsap.to('.blob-1', {
        x: 50,
        y: -30,
        duration: 8,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      });

      gsap.to('.blob-2', {
        x: -40,
        y: 40,
        duration: 10,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      });

      gsap.to('.blob-3', {
        x: 30,
        y: 50,
        duration: 12,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      });

      // Feature cards scroll animation
      gsap.from('.feature-card', {
        y: 80,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: featuresRef.current,
          start: 'top 80%',
        },
      });

      // Nearby section
      gsap.from('.nearby-content', {
        x: -80,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: nearbyRef.current,
          start: 'top 75%',
        },
      });

      gsap.from('.nearby-visual', {
        x: 80,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: nearbyRef.current,
          start: 'top 75%',
        },
      });

      // How it works
      gsap.from('.step-card', {
        y: 60,
        opacity: 0,
        duration: 0.8,
        stagger: 0.2,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: howItWorksRef.current,
          start: 'top 75%',
        },
      });

      // CTA section
      gsap.from('.cta-content', {
        scale: 0.9,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: '.cta-section',
          start: 'top 80%',
        },
      });
    });

    return () => {
      ctx.revert();
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const navItems = [
    { id: 'home', icon: Home, label: 'Home', href: '#hero' },
    { id: 'features', icon: Star, label: 'Features', href: '#features' },
    { id: 'nearby', icon: Compass, label: 'Nearby', href: '#nearby' },
    { id: 'how', icon: Info, label: 'How it Works', href: '#how-it-works' },
    { id: 'login', icon: LogIn, label: 'Login', href: '/login' },
    { id: 'signup', icon: UserPlus, label: 'Signup', href: '/signup' },
  ];

  const scrollToSection = (href) => {
    if (href.startsWith('#')) {
      const element = document.querySelector(href);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <CustomCursor />

      {/* Animated Background Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="blob-1 absolute top-[10%] left-[10%] w-[500px] h-[500px] rounded-full bg-purple-200/40 blur-[100px]" />
        <div className="blob-2 absolute top-[40%] right-[5%] w-[400px] h-[400px] rounded-full bg-pink-200/40 blur-[100px]" />
        <div className="blob-3 absolute bottom-[10%] left-[30%] w-[600px] h-[600px] rounded-full bg-purple-100/50 blur-[120px]" />
      </div>

      {/* Left Side Navigation */}
      <nav className={`fixed left-0 top-0 h-full z-50 bg-white/90 backdrop-blur-xl border-r border-gray-100 transition-all duration-300 hidden lg:flex flex-col ${navCollapsed ? 'w-20' : 'w-64'}`}>
        {/* Logo */}
        <div className={`p-6 border-b border-gray-100 flex items-center ${navCollapsed ? 'justify-center' : 'gap-3'}`}>
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
            <Heart size={24} className="text-white" fill="white" />
          </div>
          {!navCollapsed && <span className="text-xl font-bold text-gray-900">TrueBond</span>}
        </div>

        {/* Nav Items */}
        <div className="flex-1 py-6 px-3 space-y-2">
          {navItems.slice(0, 4).map((item) => (
            <a
              key={item.id}
              href={item.href}
              onClick={(e) => {
                if (item.href.startsWith('#')) {
                  e.preventDefault();
                  scrollToSection(item.href);
                }
              }}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-purple-50 hover:text-purple-600 transition-all group ${navCollapsed ? 'justify-center' : ''}`}
            >
              <item.icon size={22} className="flex-shrink-0 group-hover:scale-110 transition-transform" />
              {!navCollapsed && <span className="font-medium">{item.label}</span>}
            </a>
          ))}
        </div>

        {/* Auth Buttons */}
        <div className={`p-4 border-t border-gray-100 space-y-2 ${navCollapsed ? 'px-2' : ''}`}>
          <Link
            to="/login"
            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 hover:bg-gray-100 transition-all ${navCollapsed ? 'justify-center' : ''}`}
          >
            <LogIn size={22} />
            {!navCollapsed && <span className="font-medium">Login</span>}
          </Link>
          <Link
            to="/signup"
            className={`flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white transition-all ${navCollapsed ? 'justify-center' : ''}`}
          >
            <UserPlus size={22} />
            {!navCollapsed && <span className="font-medium">Sign Up</span>}
          </Link>
        </div>

        {/* Collapse Toggle */}
        <button
          onClick={() => setNavCollapsed(!navCollapsed)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-white border border-gray-200 flex items-center justify-center text-gray-400 hover:text-purple-500 shadow-sm"
        >
          {navCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </nav>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-t border-gray-100 px-4 py-2 safe-area-pb">
        <div className="flex justify-around">
          {navItems.slice(0, 4).map((item) => (
            <a
              key={item.id}
              href={item.href}
              onClick={(e) => {
                if (item.href.startsWith('#')) {
                  e.preventDefault();
                  scrollToSection(item.href);
                }
              }}
              className="flex flex-col items-center gap-1 px-3 py-2 text-gray-400 hover:text-purple-600 transition-colors"
            >
              <item.icon size={22} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </a>
          ))}
          <Link
            to="/login"
            className="flex flex-col items-center gap-1 px-3 py-2 text-purple-600"
          >
            <LogIn size={22} />
            <span className="text-[10px] font-medium">Login</span>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${navCollapsed ? 'lg:ml-20' : 'lg:ml-64'}`}>
        
        {/* HERO SECTION - Full Viewport */}
        <section id="hero" ref={heroRef} className="min-h-screen flex items-center relative overflow-hidden px-6 lg:px-16">
          <div className="max-w-7xl mx-auto w-full">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              {/* Left Content */}
              <div className="relative z-10">
                <div className="hero-badge inline-flex items-center gap-2 px-5 py-2.5 bg-purple-100 rounded-full mb-8">
                  <Sparkles size={18} className="text-purple-600" />
                  <span className="text-sm font-semibold text-purple-700">Find your perfect match</span>
                </div>

                <h1 className="hero-title text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-extrabold leading-[1.1] mb-8">
                  Real
                  <br />
                  connections
                  <br />
                  <span className="gradient-text">start here</span>
                </h1>

                <p className="hero-subtitle text-xl lg:text-2xl text-gray-600 mb-12 max-w-xl leading-relaxed">
                  Discover people nearby, spark meaningful conversations, and build authentic relationships that last a lifetime.
                </p>

                <div className="flex flex-wrap gap-4 hero-cta">
                  <Link to="/signup" className="btn-primary text-lg px-10 py-5 flex items-center gap-3 shadow-xl shadow-purple-300/30">
                    Start Free <ArrowRight size={22} />
                  </Link>
                  <Link to="/login" className="btn-secondary text-lg px-10 py-5">
                    I have an account
                  </Link>
                </div>

                <div className="flex items-center gap-12 mt-16 hero-cta">
                  {[
                    { value: '10', label: 'Free coins' },
                    { value: '50km', label: 'Discovery' },
                    { value: '100%', label: 'Privacy' },
                  ].map((stat, i) => (
                    <div key={i}>
                      <div className="text-3xl font-bold text-purple-600">{stat.value}</div>
                      <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right Visual */}
              <div className="hero-visual relative hidden lg:block">
                <div className="relative w-full max-w-lg mx-auto">
                  {/* Main Phone */}
                  <div className="bg-white rounded-[3rem] p-4 shadow-2xl shadow-purple-200/50">
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-[2.5rem] p-8 aspect-[9/16] relative overflow-hidden">
                      <div className="space-y-4">
                        <div className="flex gap-3">
                          {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="story-bubble">
                              <div className="story-bubble-inner bg-gradient-to-br from-purple-300 to-pink-300" />
                            </div>
                          ))}
                        </div>
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="bg-white rounded-2xl p-4 shadow-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400" />
                              <div className="flex-1">
                                <div className="h-3 w-24 bg-gray-200 rounded" />
                                <div className="h-2 w-16 bg-gray-100 rounded mt-2" />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Floating Cards */}
                  <div className="floating-card float-1 absolute -left-16 top-1/4 bg-white rounded-2xl p-5 shadow-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                        <Users size={24} className="text-green-600" />
                      </div>
                      <div>
                        <div className="text-lg font-bold">5 nearby</div>
                        <div className="text-sm text-gray-500">Looking for you</div>
                      </div>
                    </div>
                  </div>

                  <div className="floating-card float-2 absolute -right-12 top-1/2 bg-white rounded-2xl p-5 shadow-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                        <Heart size={24} className="text-purple-600" fill="currentColor" />
                      </div>
                      <div>
                        <div className="text-lg font-bold">New match!</div>
                        <div className="text-sm text-gray-500">Say hello 👋</div>
                      </div>
                    </div>
                  </div>

                  <div className="floating-card float-3 absolute -left-8 bottom-1/4 bg-white rounded-2xl p-5 shadow-xl">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center">
                        <MessageCircle size={24} className="text-pink-600" />
                      </div>
                      <div>
                        <div className="text-lg font-bold">12 messages</div>
                        <div className="text-sm text-gray-500">Unread chats</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scroll Indicator */}
          <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-400">
            <span className="text-sm">Scroll to explore</span>
            <div className="w-6 h-10 rounded-full border-2 border-gray-300 flex items-start justify-center p-2">
              <div className="w-1.5 h-3 bg-purple-500 rounded-full animate-bounce" />
            </div>
          </div>
        </section>

        {/* FEATURES SECTION */}
        <section id="features" ref={featuresRef} className="py-32 px-6 lg:px-16 bg-gradient-to-b from-white to-purple-50/30">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
                Why choose <span className="gradient-text">TrueBond</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Everything you need to find meaningful connections, all in one place
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                { icon: MapPin, title: 'Live Location', desc: 'Find people near you in real-time with precise location', color: 'from-blue-500 to-cyan-500', bg: 'bg-blue-50' },
                { icon: MessageCircle, title: 'Smart Chat', desc: 'Connect meaningfully with 1 coin per message', color: 'from-purple-500 to-pink-500', bg: 'bg-purple-50' },
                { icon: Shield, title: 'Privacy First', desc: 'Your address stays private, always protected', color: 'from-green-500 to-emerald-500', bg: 'bg-green-50' },
                { icon: Coins, title: 'Fair Pricing', desc: 'Start with 10 free coins, pay as you connect', color: 'from-amber-500 to-orange-500', bg: 'bg-amber-50' },
              ].map((feature, i) => (
                <div key={i} className={`feature-card ${feature.bg} rounded-3xl p-8 hover:shadow-xl transition-all duration-300 hover:-translate-y-2`}>
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6`}>
                    <feature.icon size={32} className="text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-3 text-gray-900">{feature.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* NEARBY SECTION */}
        <section id="nearby" ref={nearbyRef} className="py-32 px-6 lg:px-16">
          <div className="max-w-7xl mx-auto">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="nearby-content">
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-8">
                  Find people
                  <br />
                  <span className="gradient-text">near you</span>
                </h2>
                <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                  Our live map shows you interesting people in your area. See who's online, check their profile, and start a conversation.
                </p>
                <ul className="space-y-4 mb-10">
                  {[
                    'Real-time location updates',
                    'Filter by preferences',
                    'See who viewed your profile',
                    'Privacy controls you can trust',
                  ].map((item, i) => (
                    <li key={i} className="flex items-center gap-3 text-gray-700">
                      <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-purple-500" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
                <Link to="/signup" className="btn-primary inline-flex items-center gap-2">
                  Explore Nearby <ArrowRight size={20} />
                </Link>
              </div>
              <div className="nearby-visual">
                <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-3xl p-8 aspect-square flex items-center justify-center">
                  <div className="relative w-full h-full">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-32 h-32 rounded-full bg-purple-500/20 animate-ping" />
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white">
                        <MapPin size={40} />
                      </div>
                    </div>
                    {[...Array(6)].map((_, i) => (
                      <div
                        key={i}
                        className="absolute w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center"
                        style={{
                          top: `${20 + Math.random() * 60}%`,
                          left: `${10 + Math.random() * 80}%`,
                          animationDelay: `${i * 0.5}s`,
                        }}
                      >
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-300 to-pink-300" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how-it-works" ref={howItWorksRef} className="py-32 px-6 lg:px-16 bg-white">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
                Get started in <span className="gradient-text">3 steps</span>
              </h2>
              <p className="text-xl text-gray-600">Simple, fast, and secure</p>
            </div>

            <div className="grid md:grid-cols-3 gap-12">
              {[
                { num: '01', title: 'Create Profile', desc: 'Sign up in minutes. Add your photos and tell us about yourself. Your privacy is always protected.' },
                { num: '02', title: 'Discover Nearby', desc: 'Find interesting people around you on our live map. Filter by your preferences and interests.' },
                { num: '03', title: 'Start Chatting', desc: 'Send a message and start your journey together. Use coins to connect with people you like.' },
              ].map((step, i) => (
                <div key={i} className="step-card text-center">
                  <div className="text-8xl font-black text-purple-100 mb-6">{step.num}</div>
                  <h3 className="text-2xl font-bold mb-4 text-gray-900">{step.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA SECTION */}
        <section className="cta-section py-32 px-6 lg:px-16">
          <div className="max-w-5xl mx-auto">
            <div className="cta-content bg-gradient-to-br from-purple-500 via-purple-600 to-pink-500 rounded-[3rem] p-12 lg:p-20 text-white text-center relative overflow-hidden">
              <div className="absolute inset-0 opacity-20">
                <div className="absolute top-10 left-10 w-40 h-40 rounded-full bg-white blur-3xl" />
                <div className="absolute bottom-10 right-10 w-60 h-60 rounded-full bg-white blur-3xl" />
              </div>
              <div className="relative z-10">
                <Heart size={64} className="mx-auto mb-8" fill="white" />
                <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">Ready to find your bond?</h2>
                <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
                  Join thousands finding meaningful connections every day. Your perfect match could be just around the corner.
                </p>
                <Link to="/signup" className="inline-block bg-white text-purple-600 font-bold px-12 py-5 rounded-full hover:shadow-2xl transition-all text-lg">
                  Get Started Free
                </Link>
                <p className="text-white/70 text-sm mt-6">10 free coins • No credit card required</p>
              </div>
            </div>
          </div>
        </section>

        {/* FOOTER */}
        <footer className="py-12 px-6 lg:px-16 border-t border-gray-100 bg-white">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <Heart size={20} className="text-white" fill="white" />
              </div>
              <span className="text-xl font-bold text-gray-900">TrueBond</span>
            </div>
            <p className="text-gray-500">
              © {new Date().getFullYear()} TrueBond. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default LandingPage;
