import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Search, Sparkles } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const HeroSection = ({ onJoinClick, onLoginClick }) => {
  const sectionRef = useRef(null);
  const titleRef = useRef(null);
  const subtitleRef = useRef(null);
  const ctaRef = useRef(null);
  const orbitRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Title animation
      gsap.from(titleRef.current, {
        y: 100,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
        delay: 0.5,
      });

      // Subtitle animation
      gsap.from(subtitleRef.current, {
        y: 50,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        delay: 0.8,
      });

      // CTA buttons animation
      gsap.from(ctaRef.current.children, {
        y: 30,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
        delay: 1.1,
      });

      // Orbit animation
      gsap.to(orbitRef.current, {
        rotation: 360,
        duration: 60,
        repeat: -1,
        ease: 'none',
      });

      // Parallax on scroll
      gsap.to(titleRef.current, {
        yPercent: -50,
        opacity: 0,
        ease: 'none',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={sectionRef}
      className="section min-h-screen relative overflow-hidden pt-20"
    >
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-purple-900/20 via-transparent to-transparent" />
      
      {/* Animated orbs */}
      <div ref={orbitRef} className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '-3s' }} />
        <div className="absolute top-1/2 right-1/3 w-48 h-48 bg-purple-400/10 rounded-full blur-2xl animate-float" style={{ animationDelay: '-1.5s' }} />
      </div>

      {/* Decorative rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[600px] h-[600px] border border-white/5 rounded-full" />
        <div className="absolute w-[800px] h-[800px] border border-white/3 rounded-full" />
        <div className="absolute w-[1000px] h-[1000px] border border-white/2 rounded-full" />
      </div>

      {/* Content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto px-6">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10 mb-8">
          <Sparkles size={16} className="text-purple-400" />
          <span className="text-sm text-white/80">Find real connections</span>
        </div>

        <h1
          ref={titleRef}
          className="text-5xl md:text-7xl lg:text-8xl font-bold leading-tight mb-8"
        >
          <span className="text-white">Real connections</span>
          <br />
          <span className="gradient-text">start with TrueBond</span>
        </h1>

        <p
          ref={subtitleRef}
          className="text-xl md:text-2xl text-white/60 max-w-2xl mx-auto mb-12"
        >
          Discover people nearby, spark meaningful conversations, and build authentic relationships.
        </p>

        <div ref={ctaRef} className="flex flex-col sm:flex-row gap-4 justify-center">
          <button onClick={onJoinClick} className="btn-primary text-lg px-10 py-5 flex items-center justify-center gap-3">
            <Search size={20} />
            Join Now — It's Free
          </button>
          <button onClick={onLoginClick} className="btn-secondary text-lg px-10 py-5">
            I have an account
          </button>
        </div>

        {/* Stats */}
        <div className="flex justify-center gap-12 mt-20">
          {[
            { value: '10', label: 'Free coins on signup' },
            { value: '5km', label: 'Discover nearby' },
            { value: '100%', label: 'Privacy focused' },
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl md:text-4xl font-bold gradient-text">{stat.value}</div>
              <div className="text-white/40 text-sm mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2">
        <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center pt-2">
          <div className="w-1.5 h-3 bg-white/60 rounded-full animate-bounce" />
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
