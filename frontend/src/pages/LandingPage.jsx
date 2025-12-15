import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, Home, Star, Shield, HelpCircle, CreditCard, Sparkles, MapPin, MessageCircle, Video, BadgeCheck, Bell, Lock, Eye, UserCheck, Flag, ChevronDown, ChevronUp, Mail, MessageSquare, Headphones, Coins, ArrowRight, Phone, Users, Zap } from 'lucide-react';
import CustomCursor from '@/components/CustomCursor';
import AuthModal from '@/components/AuthModal';

gsap.registerPlugin(ScrollTrigger);

const LandingPage = () => {
  const [activeSection, setActiveSection] = useState('home');
  const [authModal, setAuthModal] = useState({ open: false, mode: 'login' });
  const [openFaq, setOpenFaq] = useState(null);
  const containerRef = useRef(null);

  const navItems = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'features', icon: Star, label: 'Features' },
    { id: 'safety', icon: Shield, label: 'Safety' },
    { id: 'support', icon: HelpCircle, label: 'Support' },
    { id: 'pricing', icon: CreditCard, label: 'Pricing' },
  ];

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Hero animations
      gsap.from('.hero-badge', { y: -40, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.2 });
      gsap.from('.hero-title', { y: 60, opacity: 0, duration: 1.2, ease: 'power3.out', delay: 0.4 });
      gsap.from('.hero-subtitle', { y: 40, opacity: 0, duration: 1, ease: 'power3.out', delay: 0.6 });
      gsap.from('.hero-cta', { y: 30, opacity: 0, duration: 0.8, stagger: 0.15, ease: 'power3.out', delay: 0.8 });
      gsap.from('.hero-float', { y: 80, opacity: 0, duration: 1, stagger: 0.2, ease: 'power3.out', delay: 1 });

      // Floating animation loops
      gsap.to('.float-1', { y: -20, duration: 3, ease: 'sine.inOut', yoyo: true, repeat: -1 });
      gsap.to('.float-2', { y: -15, duration: 2.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 0.5 });
      gsap.to('.float-3', { y: -25, duration: 3.5, ease: 'sine.inOut', yoyo: true, repeat: -1, delay: 1 });

      // Section scroll animations
      const sections = ['features', 'safety', 'support', 'pricing', 'connect'];
      sections.forEach((section) => {
        gsap.from(`#${section} .section-title`, {
          y: 50, opacity: 0, duration: 0.8, ease: 'power3.out',
          scrollTrigger: { trigger: `#${section}`, start: 'top 80%' }
        });
        gsap.from(`#${section} .section-content`, {
          y: 60, opacity: 0, duration: 0.8, stagger: 0.1, ease: 'power3.out',
          scrollTrigger: { trigger: `#${section}`, start: 'top 75%' }
        });
      });

      // Parallax backgrounds
      gsap.to('.parallax-bg', {
        yPercent: 20,
        ease: 'none',
        scrollTrigger: { trigger: '.parallax-bg', start: 'top bottom', end: 'bottom top', scrub: true }
      });

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
    }, containerRef);

    return () => ctx.revert();
  }, []);

  const features = [
    { icon: Sparkles, title: 'AI-Powered Matching', desc: 'Smart algorithms find your perfect match based on personality, interests, and compatibility scores.' },
    { icon: MapPin, title: 'Snap Map Discovery', desc: 'See who\'s nearby in real-time. Discover connections within your preferred distance range.' },
    { icon: MessageCircle, title: 'Real-Time Messaging', desc: 'Instant messaging with read receipts, typing indicators, and rich media sharing.' },
    { icon: Video, title: 'Voice & Video Calls', desc: 'Connect face-to-face with HD video calls. Break the ice before meeting in person.' },
    { icon: BadgeCheck, title: 'Verified Profiles', desc: 'Photo and ID verification ensures you\'re connecting with real, authentic people.' },
    { icon: Bell, title: 'Smart Notifications', desc: 'Never miss a match or message with intelligent, non-intrusive notifications.' },
  ];

  const safetyFeatures = [
    { icon: Eye, title: 'Photo Verification', desc: 'AI-powered selfie verification confirms users match their profile photos.' },
    { icon: UserCheck, title: 'ID Verification', desc: 'Optional government ID verification for enhanced trust and safety.' },
    { icon: Lock, title: 'End-to-End Encryption', desc: 'All messages are encrypted. Your conversations stay private.' },
    { icon: Flag, title: 'Block & Report', desc: 'Easily block or report suspicious behavior. Our team reviews reports 24/7.' },
    { icon: Shield, title: 'Privacy-First Design', desc: 'Your location and personal data are never shared without your consent.' },
  ];

  const faqs = [
    { q: 'How does TrueBond matching work?', a: 'Our AI analyzes your preferences, behavior, and compatibility factors to suggest matches most likely to lead to meaningful connections.' },
    { q: 'Is my data safe?', a: 'Absolutely. We use bank-level encryption and never sell your data. You control what\'s visible on your profile.' },
    { q: 'What are coins used for?', a: 'Coins let you send messages, boost your profile visibility, and unlock premium features. New users get 10 free coins!' },
    { q: 'How do I verify my profile?', a: 'Simply take a selfie matching a random pose. Our AI confirms it\'s really you within seconds.' },
  ];

  const pricingPlans = [
    { coins: 50, price: 49, perCoin: '0.98', popular: false },
    { coins: 100, price: 89, perCoin: '0.89', popular: true },
    { coins: 250, price: 199, perCoin: '0.80', popular: false },
    { coins: 500, price: 349, perCoin: '0.70', popular: false },
  ];

  return (
    <div ref={containerRef} className="min-h-screen bg-white">
      <CustomCursor />

      {/* LEFT FLOATING NAV */}
      <nav className="fixed left-6 top-1/2 -translate-y-1/2 z-50 hidden lg:block">
        <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-3 shadow-xl border border-white/50">
          <div className="space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all group ${
                  activeSection === item.id
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                    : 'text-gray-600 hover:bg-purple-50 hover:text-purple-600'
                }`}
              >
                <item.icon size={20} className={activeSection === item.id ? '' : 'group-hover:scale-110 transition-transform'} />
                <span className="font-medium text-sm">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* TOP-RIGHT AUTH BUTTONS */}
      <div className="fixed top-6 right-6 z-50 flex items-center gap-3">
        <button
          onClick={() => setAuthModal({ open: true, mode: 'login' })}
          className="px-6 py-2.5 text-gray-700 font-medium hover:text-purple-600 transition-colors bg-white/80 backdrop-blur-lg rounded-full border border-gray-200 hover:border-purple-300"
        >
          Login
        </button>
        <button
          onClick={() => setAuthModal({ open: true, mode: 'signup' })}
          className="px-6 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105"
        >
          Sign Up
        </button>
      </div>

      {/* MOBILE BOTTOM NAV */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-t border-gray-100 px-2 py-2 safe-area-pb">
        <div className="flex justify-around">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className={`flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-colors ${
                activeSection === item.id ? 'text-purple-600' : 'text-gray-400'
              }`}
            >
              <item.icon size={20} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section id="home" className="relative min-h-screen flex items-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 parallax-bg">
          <img
            src="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-purple-900/80 via-purple-800/70 to-pink-900/60" />
          <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-16 py-32 lg:ml-32">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="hero-badge inline-flex items-center gap-2 px-5 py-2.5 bg-white/20 backdrop-blur-lg rounded-full mb-8 border border-white/30">
                <Heart size={18} className="text-pink-300" fill="currentColor" />
                <span className="text-sm font-medium text-white">Trusted by 100,000+ singles</span>
              </div>

              <h1 className="hero-title text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold leading-[1.1] mb-8 text-white">
                Making meaningful
                <br />
                connections
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-300 to-purple-300">since 2024</span>
              </h1>

              <p className="hero-subtitle text-xl lg:text-2xl text-white/80 mb-10 max-w-xl leading-relaxed">
                We exist to bring people closer to love. Discover genuine connections with verified profiles, smart matching, and secure messaging.
              </p>

              <div className="flex flex-wrap gap-4 hero-cta">
                <button
                  onClick={() => setAuthModal({ open: true, mode: 'signup' })}
                  className="px-8 py-4 bg-white text-purple-600 font-bold rounded-full shadow-xl hover:shadow-2xl transition-all hover:scale-105 flex items-center gap-2"
                >
                  Get Started Free <ArrowRight size={20} />
                </button>
                <button className="px-8 py-4 bg-white/20 backdrop-blur-lg text-white font-medium rounded-full border border-white/30 hover:bg-white/30 transition-all flex items-center gap-2">
                  <Video size={20} /> Watch Demo
                </button>
              </div>
            </div>

            {/* Floating UI Elements */}
            <div className="hidden lg:block relative">
              <div className="hero-float float-1 absolute top-0 right-0 bg-white rounded-2xl p-5 shadow-2xl">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-400 to-pink-400" />
                  <div>
                    <div className="font-bold text-gray-900">New Match!</div>
                    <div className="text-sm text-gray-500">Sarah liked you 💖</div>
                  </div>
                </div>
              </div>

              <div className="hero-float float-2 absolute top-1/3 left-0 bg-white rounded-2xl p-5 shadow-2xl">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                    <MessageCircle size={24} className="text-green-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">12 Messages</div>
                    <div className="text-sm text-gray-500">3 unread chats</div>
                  </div>
                </div>
              </div>

              <div className="hero-float float-3 absolute bottom-1/4 right-10 bg-white rounded-2xl p-5 shadow-2xl">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                    <Users size={24} className="text-purple-600" />
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">8 Nearby</div>
                    <div className="text-sm text-gray-500">Within 5km</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-white/60">
          <span className="text-sm">Scroll to explore</span>
          <div className="w-6 h-10 rounded-full border-2 border-white/40 flex items-start justify-center p-2">
            <div className="w-1.5 h-3 bg-white rounded-full animate-bounce" />
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section id="features" className="relative py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover opacity-10"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-white via-purple-50/80 to-white" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-16 lg:ml-32">
          <div className="text-center mb-16">
            <h2 className="section-title text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              Powerful <span className="gradient-text">Features</span>
            </h2>
            <p className="section-content text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to find meaningful connections, all in one beautifully designed app.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <div
                key={i}
                className="section-content bg-white rounded-3xl p-8 shadow-lg hover:shadow-xl transition-all hover:-translate-y-2 border border-purple-100"
              >
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-6">
                  <feature.icon size={32} className="text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== SAFETY SECTION ===== */}
      <section id="safety" className="relative py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/95 to-white/90" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-16 lg:ml-32">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="section-title text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
                Your <span className="gradient-text">Safety</span>
                <br />comes first
              </h2>
              <p className="section-content text-xl text-gray-600 mb-10 leading-relaxed">
                We've built industry-leading safety features to ensure you can focus on what matters most — finding genuine connections.
              </p>

              <div className="space-y-6">
                {safetyFeatures.map((feature, i) => (
                  <div key={i} className="section-content flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
                      <feature.icon size={24} className="text-green-600" />
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900 mb-1">{feature.title}</h4>
                      <p className="text-gray-600">{feature.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="section-content hidden lg:block">
              <div className="relative">
                <div className="bg-gradient-to-br from-green-100 to-blue-100 rounded-3xl p-12 aspect-square flex items-center justify-center">
                  <div className="relative">
                    <div className="w-48 h-48 rounded-full bg-white shadow-2xl flex items-center justify-center">
                      <Shield size={80} className="text-green-500" />
                    </div>
                    <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full bg-green-500 flex items-center justify-center shadow-lg">
                      <BadgeCheck size={32} className="text-white" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SUPPORT SECTION ===== */}
      <section id="support" className="relative py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1553877522-43269d4ea984?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover opacity-15"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-purple-50 via-white to-purple-50" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-16 lg:ml-32">
          <div className="text-center mb-16">
            <h2 className="section-title text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
              We're here to <span className="gradient-text">Help</span>
            </h2>
            <p className="section-content text-xl text-gray-600 max-w-2xl mx-auto">
              Our support team is available 24/7 to assist you with any questions or concerns.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* FAQ */}
            <div className="section-content">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h3>
              <div className="space-y-4">
                {faqs.map((faq, i) => (
                  <div key={i} className="bg-white rounded-2xl border border-purple-100 overflow-hidden">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between p-5 text-left"
                    >
                      <span className="font-semibold text-gray-900">{faq.q}</span>
                      {openFaq === i ? <ChevronUp size={20} className="text-purple-500" /> : <ChevronDown size={20} className="text-gray-400" />}
                    </button>
                    {openFaq === i && (
                      <div className="px-5 pb-5 text-gray-600">{faq.a}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Contact Options */}
            <div className="section-content space-y-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Get in Touch</h3>
              
              <div className="bg-white rounded-2xl p-6 border border-purple-100 hover:shadow-lg transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-purple-100 flex items-center justify-center">
                    <MessageSquare size={28} className="text-purple-600" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">Live Chat</h4>
                    <p className="text-gray-600">Chat with our team in real-time</p>
                  </div>
                  <ArrowRight size={20} className="ml-auto text-purple-500" />
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-purple-100 hover:shadow-lg transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-pink-100 flex items-center justify-center">
                    <Mail size={28} className="text-pink-600" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">Email Support</h4>
                    <p className="text-gray-600">support@truebond.com</p>
                  </div>
                  <ArrowRight size={20} className="ml-auto text-pink-500" />
                </div>
              </div>

              <div className="bg-white rounded-2xl p-6 border border-purple-100 hover:shadow-lg transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-blue-100 flex items-center justify-center">
                    <Headphones size={28} className="text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">Help Center</h4>
                    <p className="text-gray-600">Browse our knowledge base</p>
                  </div>
                  <ArrowRight size={20} className="ml-auto text-blue-500" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== PRICING SECTION ===== */}
      <section id="pricing" className="relative py-32 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/90 via-purple-800/85 to-pink-900/90" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-16 lg:ml-32">
          <div className="text-center mb-16">
            <h2 className="section-title text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 text-white">
              Simple <span className="text-transparent bg-clip-text bg-gradient-to-r from-pink-300 to-purple-300">Pricing</span>
            </h2>
            <p className="section-content text-xl text-white/80 max-w-2xl mx-auto">
              Get 10 free coins on signup! Use coins to send messages and unlock premium features.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {pricingPlans.map((plan, i) => (
              <div
                key={i}
                className={`section-content rounded-3xl p-8 transition-all hover:-translate-y-2 ${
                  plan.popular
                    ? 'bg-white shadow-2xl scale-105'
                    : 'bg-white/10 backdrop-blur-lg border border-white/20'
                }`}
              >
                {plan.popular && (
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-bold px-3 py-1 rounded-full inline-block mb-4">
                    MOST POPULAR
                  </div>
                )}
                <div className="flex items-center gap-2 mb-4">
                  <Coins size={28} className={plan.popular ? 'text-purple-500' : 'text-white'} />
                  <span className={`text-3xl font-bold ${plan.popular ? 'text-gray-900' : 'text-white'}`}>{plan.coins}</span>
                  <span className={plan.popular ? 'text-gray-500' : 'text-white/60'}>coins</span>
                </div>
                <div className={`text-4xl font-bold mb-2 ${plan.popular ? 'text-gray-900' : 'text-white'}`}>
                  ₹{plan.price}
                </div>
                <div className={`text-sm mb-6 ${plan.popular ? 'text-gray-500' : 'text-white/60'}`}>
                  ₹{plan.perCoin} per coin
                </div>
                <button
                  onClick={() => setAuthModal({ open: true, mode: 'signup' })}
                  className={`w-full py-3 rounded-xl font-semibold transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg'
                      : 'bg-white/20 text-white hover:bg-white/30'
                  }`}
                >
                  Get Started
                </button>
              </div>
            ))}
          </div>

          <div className="section-content text-center mt-12">
            <p className="text-white/60">1 coin = 1 message • Coins never expire • Secure payment via Razorpay</p>
          </div>
        </div>
      </section>

      {/* ===== CONNECT SECTION ===== */}
      <section id="connect" className="relative py-32 overflow-hidden">
        {/* Background Image - Hands Reaching */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?w=1920&q=80"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-purple-900/80 via-purple-800/60 to-transparent" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-6 lg:px-16 text-center">
          <div className="section-title">
            <Heart size={64} className="mx-auto mb-8 text-pink-400" fill="currentColor" />
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 text-white">
              Let's get connected
            </h2>
          </div>
          <p className="section-content text-xl text-white/80 mb-10 max-w-2xl mx-auto leading-relaxed">
            Your perfect match could be just around the corner. Join thousands who've found love on TrueBond. Start your journey today.
          </p>
          <button
            onClick={() => setAuthModal({ open: true, mode: 'signup' })}
            className="section-content px-10 py-5 bg-white text-purple-600 font-bold text-lg rounded-full shadow-2xl hover:shadow-3xl transition-all hover:scale-105 inline-flex items-center gap-3"
          >
            Find Your Bond <ArrowRight size={24} />
          </button>
          <p className="section-content text-white/60 mt-6">Free to join • 10 coins on signup • Cancel anytime</p>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="bg-gray-900 py-12 px-6 lg:px-16">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6 lg:ml-32">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-white">TrueBond</span>
          </div>
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} TrueBond. All rights reserved. Made with ❤️ in India.
          </p>
        </div>
      </footer>

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
