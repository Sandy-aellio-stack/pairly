import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, ArrowRight } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const CTASection = ({ onJoinClick }) => {
  const sectionRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(contentRef.current, {
        y: 80,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 70%',
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="section py-32 px-6 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-t from-purple-900/30 via-transparent to-transparent" />
      
      {/* Decorative elements */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl" />

      <div ref={contentRef} className="max-w-4xl mx-auto text-center relative z-10">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 mb-8 animate-pulse-purple">
          <Heart size={40} className="text-white" fill="white" />
        </div>

        <h2 className="text-4xl md:text-5xl lg:text-7xl font-bold mb-6">
          Create your
          <br />
          <span className="gradient-text">TrueBond</span>
        </h2>

        <p className="text-xl text-white/60 max-w-xl mx-auto mb-12">
          Join thousands of people finding meaningful connections every day. Your perfect match might be just around the corner.
        </p>

        <button
          onClick={onJoinClick}
          className="btn-primary text-xl px-12 py-6 inline-flex items-center gap-3 group"
        >
          Get Started Free
          <ArrowRight size={24} className="group-hover:translate-x-2 transition-transform" />
        </button>

        <p className="text-white/40 mt-6">
          10 free coins • No credit card required
        </p>
      </div>
    </section>
  );
};

export default CTASection;
