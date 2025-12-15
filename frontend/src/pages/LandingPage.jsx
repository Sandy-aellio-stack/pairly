import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, Home, Star, Shield, HelpCircle, CreditCard, Sparkles, MapPin, MessageCircle, Video, BadgeCheck, Bell, Lock, Eye, UserCheck, Flag, ChevronDown, ChevronUp, Mail, MessageSquare, Headphones, Coins, ArrowRight, Phone, Users, Zap, Filter, ThumbsUp, UserPlus, Search, AlertTriangle, Check } from 'lucide-react';
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

  const mainFeatures = [
    { icon: MapPin, title: 'Snap Map Style Discovery', desc: "See nearby users on an interactive map. Discover people around you in real-time with our location-based matching." },
    { icon: Sparkles, title: 'AI-Powered Matching', desc: 'Our intelligent algorithm learns your preferences and suggests compatible matches based on interests, values, and behavior.' },
    { icon: Video, title: 'Video & Voice Calls', desc: 'Connect face-to-face with video calls or have voice conversations before meeting in person.' },
    { icon: BadgeCheck, title: 'Verified Profiles', desc: "Photo verification and ID checks ensure you're talking to real people. Safety is our top priority." },
    { icon: MessageCircle, title: 'Real-Time Messaging', desc: 'Instant messaging with read receipts, typing indicators, and rich media sharing.' },
  ];

  const moreFeatures = [
    { icon: Bell, title: 'Smart Notifications' },
    { icon: Lock, title: 'End-to-End Encryption' },
    { icon: Filter, title: 'Advanced Filters' },
    { icon: ThumbsUp, title: 'Super Likes' },
    { icon: Users, title: 'Group Chats' },
    { icon: Zap, title: 'Boost Profile' },
  ];

  const safetyFeatures = [
    { icon: Eye, title: 'Photo Verification', desc: 'AI-powered selfie verification confirms users match their profile photos.' },
    { icon: UserCheck, title: 'ID Verification', desc: 'Optional government ID verification for enhanced trust and authenticity.' },
    { icon: Lock, title: 'End-to-End Encryption', desc: 'All messages are encrypted. Your conversations stay completely private.' },
    { icon: Shield, title: 'Private Mode', desc: 'Control who sees your profile with advanced privacy settings.' },
    { icon: Flag, title: 'Easy Reporting', desc: 'Report suspicious behavior instantly. Our team reviews reports 24/7.' },
    { icon: UserPlus, title: 'Block & Unmatch', desc: 'Easily block or unmatch anyone. You are always in control.' },
  ];

  const safetyTips = [
    'Never share financial information',
    'Video chat before meeting in person',
    'Meet in public places first',
    'Tell a friend about your plans',
    'Trust your instincts',
    'Report suspicious behavior',
  ];

  const faqs = [
    { q: 'How does TrueBond matching work?', a: 'Our AI analyzes your preferences, behavior, and compatibility factors to suggest matches most likely to lead to meaningful connections.' },
    { q: 'Is my data safe?', a: 'Absolutely. We use bank-level encryption and never sell your data. You control what\'s visible on your profile.' },
    { q: 'What are coins used for?', a: 'Coins let you send messages, boost your profile visibility, and unlock premium features. New users get 10 free coins!' },
    { q: 'How do I verify my profile?', a: 'Simply take a selfie matching a random pose. Our AI confirms it\'s really you within seconds.' },
  ];

  const pricingPlans = [
    { name: 'Free', price: 0, period: '', features: ['10 free coins on signup', 'Basic matching', 'Limited daily swipes', 'View profiles'], cta: 'Get Started', popular: false },
    { name: 'Premium', price: 14.99, period: '/month', features: ['100 coins/month', 'Unlimited swipes', 'See who likes you', 'Advanced filters', 'Read receipts', 'Priority support'], cta: 'Start Premium', popular: true },
    { name: 'VIP', price: 29.99, period: '/month', features: ['300 coins/month', 'Everything in Premium', 'Profile boost weekly', 'Incognito mode', 'Super likes', 'VIP badge'], cta: 'Go VIP', popular: false },
  ];

  return (
    <div ref={containerRef} className="min-h-screen bg-white">
      <CustomCursor />

      {/* TOP HEADER - App Name Left, Auth Right */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-b border-gray-100">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12 h-16 flex items-center justify-between">
          {/* App Name - Left */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-gray-900">TrueBond</span>
          </div>

          {/* Auth Buttons - Right */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAuthModal({ open: true, mode: 'login' })}
              className="px-5 py-2 text-gray-700 font-medium hover:text-purple-600 transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => setAuthModal({ open: true, mode: 'signup' })}
              className="px-5 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              Sign Up
            </button>
          </div>
        </div>
      </header>

      {/* LEFT STATIC NAVIGATION */}
      <nav className="fixed left-6 top-1/2 -translate-y-1/2 z-40 hidden lg:block">
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl p-3 shadow-xl border border-gray-200/50">
          <div className="space-y-1">
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
                <item.icon size={18} />
                <span className="font-medium text-sm">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* MOBILE BOTTOM NAV */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-lg border-t border-gray-100 px-2 py-2 safe-area-pb">
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
      <section id="home" className="min-h-screen flex items-center justify-center relative overflow-hidden pt-16">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-pink-50" />
        <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-purple-200/30 blur-[100px]" />
        <div className="absolute bottom-1/4 left-1/4 w-80 h-80 rounded-full bg-pink-200/30 blur-[100px]" />

        <div className="relative z-10 w-full max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12 py-20 lg:py-28">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left Column - Text Content */}
            <div className="max-w-xl lg:pl-16">
              <div className="hero-badge inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full mb-6">
                <Heart size={16} className="text-purple-600" fill="currentColor" />
                <span className="text-sm font-medium text-purple-700">Trusted by 100,000+ singles</span>
              </div>

              <h1 className="hero-title text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.1] mb-6 text-gray-900">
                Making meaningful
                <br />
                connections
                <br />
                <span className="gradient-text">since 2024</span>
              </h1>

              <p className="hero-subtitle text-lg lg:text-xl text-gray-600 mb-8 leading-relaxed">
                We exist to bring people closer to love. Discover genuine connections with verified profiles, smart matching, and secure messaging.
              </p>

              <div className="flex flex-wrap gap-4 hero-cta">
                <button
                  onClick={() => setAuthModal({ open: true, mode: 'signup' })}
                  className="btn-primary px-8 py-4 flex items-center gap-2 shadow-xl shadow-purple-300/30"
                >
                  Get Started Free <ArrowRight size={20} />
                </button>
                <button className="px-8 py-4 bg-white text-gray-700 font-medium rounded-full border border-gray-200 hover:border-purple-300 hover:text-purple-600 transition-all flex items-center gap-2">
                  <Video size={20} /> Watch Demo
                </button>
              </div>
            </div>

            {/* Right Column - Hero Visual */}
            <div className="hidden lg:flex justify-center items-center">
              <div className="relative w-[320px] xl:w-[360px]">
                {/* Phone Mockup */}
                <div className="bg-white rounded-[2rem] p-3 shadow-2xl shadow-purple-200/40">
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-[1.5rem] p-5 aspect-[9/14] relative overflow-hidden">
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        {[1, 2, 3, 4].map((i) => (
                          <div key={i} className="story-bubble">
                            <div className="story-bubble-inner bg-gradient-to-br from-purple-300 to-pink-300" />
                          </div>
                        ))}
                      </div>
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-white rounded-xl p-3 shadow-md">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400" />
                            <div className="flex-1">
                              <div className="h-2.5 w-20 bg-gray-200 rounded" />
                              <div className="h-2 w-12 bg-gray-100 rounded mt-1.5" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Floating Card - Top Left */}
                <div className="hero-float float-1 absolute -left-4 xl:-left-8 top-4 bg-white rounded-xl p-3 shadow-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center">
                      <Users size={18} className="text-green-600" />
                    </div>
                    <div>
                      <div className="font-bold text-sm">5 nearby</div>
                      <div className="text-xs text-gray-500">Looking for you</div>
                    </div>
                  </div>
                </div>

                {/* Floating Card - Right */}
                <div className="hero-float float-2 absolute -right-2 xl:-right-6 top-1/3 bg-white rounded-xl p-3 shadow-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center">
                      <Heart size={18} className="text-purple-600" fill="currentColor" />
                    </div>
                    <div>
                      <div className="font-bold text-sm">New match!</div>
                      <div className="text-xs text-gray-500">Say hello 👋</div>
                    </div>
                  </div>
                </div>

                {/* Floating Card - Bottom Left */}
                <div className="hero-float float-3 absolute left-0 xl:-left-4 bottom-20 bg-white rounded-xl p-3 shadow-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 rounded-full bg-pink-100 flex items-center justify-center">
                      <MessageCircle size={18} className="text-pink-600" />
                    </div>
                    <div>
                      <div className="font-bold text-sm">12 messages</div>
                      <div className="text-xs text-gray-500">3 unread</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section id="features" className="py-20 lg:py-28 bg-gradient-to-b from-white via-purple-50/50 to-white">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Powerful <span className="gradient-text">Features</span>
            </h2>
            <p className="text-lg text-gray-600 mb-2">Everything you need to find your match</p>
            <p className="text-gray-500 max-w-2xl mx-auto">
              Discover the features that make TrueBond the most innovative dating platform.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {mainFeatures.map((feature, i) => (
              <div
                key={i}
                className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 border border-purple-100/50"
              >
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-4">
                  <feature.icon size={28} className="text-white" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>

          {/* More Features Grid */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">And so much more...</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {moreFeatures.map((feature, i) => (
                <div key={i} className="bg-white rounded-xl p-4 text-center shadow-sm hover:shadow-md transition-all">
                  <feature.icon size={24} className="text-purple-500 mx-auto mb-2" />
                  <span className="text-sm font-medium text-gray-700">{feature.title}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== SAFETY SECTION ===== */}
      <section id="safety" className="py-20 lg:py-28 bg-white">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
          <div className="text-center mb-4">
            <span className="text-sm font-medium text-purple-600 uppercase tracking-wide">Your safety matters</span>
          </div>
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Date with <span className="gradient-text">confidence</span>
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              We're committed to creating a safe space for meaningful connections. Your security is built into everything we do.
            </p>
          </div>

          {/* Safety Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
            {safetyFeatures.map((feature, i) => (
              <div
                key={i}
                className="bg-gray-50 rounded-2xl p-6 hover:bg-white hover:shadow-lg transition-all border border-gray-100"
              >
                <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center mb-4">
                  <feature.icon size={24} className="text-green-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>

          {/* Safety Tips */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-2 text-center">Safety Tips</h3>
            <p className="text-gray-500 text-center mb-6">Follow these guidelines for a safer dating experience.</p>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {safetyTips.map((tip, i) => (
                <div key={i} className="flex items-center gap-3 bg-white rounded-xl p-4">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <Check size={16} className="text-green-600" />
                  </div>
                  <span className="text-gray-700 font-medium text-sm">{tip}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Emergency Help */}
          <div className="mt-8 bg-red-50 border border-red-200 rounded-2xl p-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertTriangle size={24} className="text-red-600" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900">Need Help?</h4>
                  <p className="text-gray-600 text-sm">If you're in immediate danger, please contact emergency services.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a href="tel:911" className="px-4 py-2 bg-red-600 text-white font-medium rounded-lg flex items-center gap-2 hover:bg-red-700 transition-colors">
                  <Phone size={18} /> Emergency 911
                </a>
                <button className="px-4 py-2 bg-white text-gray-700 font-medium rounded-lg border border-gray-200 flex items-center gap-2 hover:border-red-300 transition-colors">
                  <MessageSquare size={18} /> Contact Safety Team
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SUPPORT SECTION ===== */}
      <section id="support" className="py-20 lg:py-28 bg-gradient-to-b from-purple-50/50 via-white to-white">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              How can we <span className="gradient-text">help you?</span>
            </h2>
          </div>

          {/* Search */}
          <div className="max-w-2xl mx-auto mb-12">
            <div className="relative">
              <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search for answers..."
                className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-purple-400 focus:ring-2 focus:ring-purple-100 outline-none transition-all text-gray-700"
              />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">
            {/* FAQ */}
            <div className="section-content">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h3>
              <div className="space-y-3">
                {faqs.map((faq, i) => (
                  <div key={i} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
                    >
                      <span className="font-semibold text-gray-900">{faq.q}</span>
                      {openFaq === i ? <ChevronUp size={20} className="text-purple-500" /> : <ChevronDown size={20} className="text-gray-400" />}
                    </button>
                    {openFaq === i && (
                      <div className="px-4 pb-4 text-gray-600 text-sm">{faq.a}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Contact Options */}
            <div className="section-content">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Still need help?</h3>
              <div className="space-y-4">
                <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-purple-300 hover:shadow-lg transition-all cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
                      <MessageSquare size={24} className="text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900">Live Chat</h4>
                      <p className="text-gray-500 text-sm">Chat with our support team in real-time</p>
                    </div>
                    <button className="px-4 py-2 bg-purple-500 text-white rounded-lg font-medium hover:bg-purple-600 transition-colors">
                      Start Chat
                    </button>
                  </div>
                </div>

                <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-pink-300 hover:shadow-lg transition-all cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-pink-100 flex items-center justify-center">
                      <Mail size={24} className="text-pink-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900">Email Us</h4>
                      <p className="text-gray-500 text-sm">support@truebond.com • We'll respond within 24 hours</p>
                    </div>
                    <ArrowRight size={20} className="text-gray-400" />
                  </div>
                </div>

                <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
                      <Phone size={24} className="text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900">Call Us</h4>
                      <p className="text-gray-500 text-sm">Mon-Fri, 9am-6pm IST • 1-800-TRUEBOND</p>
                    </div>
                    <ArrowRight size={20} className="text-gray-400" />
                  </div>
                </div>
              </div>

              {/* Contact Form */}
              <div className="mt-8 bg-gray-50 rounded-xl p-6">
                <h4 className="font-bold text-gray-900 mb-4">Send us a message</h4>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <input type="text" placeholder="Your name" className="input" />
                    <input type="email" placeholder="Your email" className="input" />
                  </div>
                  <input type="text" placeholder="Subject" className="input" />
                  <textarea placeholder="Tell us more..." className="input min-h-[100px] resize-none" />
                  <button className="btn-primary w-full">Send Message</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== PRICING SECTION ===== */}
      <section id="pricing" className="py-20 lg:py-28 bg-white">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Find love at <span className="gradient-text">any price</span>
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Choose the plan that's right for you. All plans include our core matching features.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {pricingPlans.map((plan, i) => (
              <div
                key={i}
                className={`section-content rounded-2xl p-6 transition-all ${
                  plan.popular
                    ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-2xl scale-105 relative'
                    : 'bg-white border border-gray-200 hover:border-purple-300 hover:shadow-lg'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-yellow-400 text-yellow-900 text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </div>
                )}
                <h3 className={`text-xl font-bold mb-2 ${plan.popular ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
                <div className="mb-6">
                  <span className={`text-4xl font-bold ${plan.popular ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price === 0 ? 'Free' : `$${plan.price}`}
                  </span>
                  {plan.period && <span className={plan.popular ? 'text-white/70' : 'text-gray-500'}>{plan.period}</span>}
                </div>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, j) => (
                    <li key={j} className="flex items-center gap-2">
                      <Check size={16} className={plan.popular ? 'text-white' : 'text-green-500'} />
                      <span className={`text-sm ${plan.popular ? 'text-white/90' : 'text-gray-600'}`}>{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => setAuthModal({ open: true, mode: 'signup' })}
                  className={`w-full py-3 rounded-xl font-semibold transition-all ${
                    plan.popular
                      ? 'bg-white text-purple-600 hover:bg-gray-100'
                      : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CONNECT SECTION ===== */}
      <section id="connect" className="py-20 lg:py-28 relative overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://customer-assets.emergentagent.com/job_bond-match/artifacts/7u34ylxt_WhatsApp%20Image%202025-12-15%20at%2015.05.44%20%282%29.jpeg"
            alt="Connection"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-purple-900/90 via-purple-800/70 to-purple-900/50" />
        </div>

        <div className="relative z-10 max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12 text-center">
          <Heart size={56} className="mx-auto mb-6 text-pink-400" fill="currentColor" />
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 text-white">
            Let's get connected
          </h2>
          <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto leading-relaxed">
            Your perfect match could be just around the corner. Join thousands who've found love on TrueBond. Start your journey today.
          </p>
          <button
            onClick={() => setAuthModal({ open: true, mode: 'signup' })}
            className="px-8 py-4 bg-white text-purple-600 font-bold rounded-full shadow-xl hover:shadow-2xl transition-all hover:scale-105 inline-flex items-center gap-2"
          >
            Find Your Bond <ArrowRight size={20} />
          </button>
          <p className="text-white/60 mt-6 text-sm">Free to join • 10 coins on signup • Cancel anytime</p>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="bg-gray-900 py-10 px-6 md:px-10 lg:px-12">
        <div className="max-w-[1400px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
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
