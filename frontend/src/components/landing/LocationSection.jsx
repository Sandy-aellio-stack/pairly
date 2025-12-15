import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { MapPin, Navigation, Users, Zap } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const LocationSection = () => {
  const sectionRef = useRef(null);
  const contentRef = useRef(null);
  const mapRef = useRef(null);
  const pinsRef = useRef([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Pin section for effect
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=100%',
        pin: true,
        pinSpacing: true,
      });

      // Content fade in
      gsap.from(contentRef.current, {
        x: -100,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 60%',
        },
      });

      // Map animation
      gsap.from(mapRef.current, {
        scale: 0.8,
        opacity: 0,
        duration: 1.2,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 60%',
        },
      });

      // Pins animation
      pinsRef.current.forEach((pin, i) => {
        gsap.from(pin, {
          scale: 0,
          opacity: 0,
          duration: 0.5,
          delay: 0.8 + i * 0.2,
          ease: 'back.out(1.7)',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 60%',
          },
        });

        // Pulse animation
        gsap.to(pin, {
          scale: 1.1,
          duration: 1,
          repeat: -1,
          yoyo: true,
          ease: 'power1.inOut',
          delay: i * 0.3,
        });
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="section min-h-screen bg-[#0B0B0F] relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
        {/* Content */}
        <div ref={contentRef}>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 rounded-full border border-purple-500/30 mb-8">
            <Navigation size={16} className="text-purple-400" />
            <span className="text-sm text-purple-300">Live Location</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Discover people
            <br />
            <span className="gradient-text">near you</span>
          </h2>

          <p className="text-xl text-white/60 mb-10 max-w-lg">
            Our live location feature helps you find and connect with interesting people in your vicinity.
          </p>

          <div className="space-y-6">
            {[
              { icon: MapPin, text: 'Real-time location updates' },
              { icon: Users, text: 'See who\'s nearby right now' },
              { icon: Zap, text: 'Instant distance calculation' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <item.icon size={24} className="text-purple-400" />
                </div>
                <span className="text-lg text-white/80">{item.text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Animated Map Illustration */}
        <div ref={mapRef} className="relative">
          <div className="aspect-square max-w-lg mx-auto relative">
            {/* Map background */}
            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-purple-900/30 to-purple-600/10 border border-purple-500/20">
              {/* Grid lines */}
              <div className="absolute inset-0 opacity-20">
                {[...Array(10)].map((_, i) => (
                  <div key={`h-${i}`} className="absolute left-0 right-0 border-t border-white/10" style={{ top: `${i * 10}%` }} />
                ))}
                {[...Array(10)].map((_, i) => (
                  <div key={`v-${i}`} className="absolute top-0 bottom-0 border-l border-white/10" style={{ left: `${i * 10}%` }} />
                ))}
              </div>

              {/* Center point (You) */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="w-16 h-16 rounded-full bg-purple-500 flex items-center justify-center animate-pulse-purple">
                  <span className="text-white font-bold">YOU</span>
                </div>
                {/* Radar rings */}
                <div className="absolute inset-0 -m-8 border-2 border-purple-500/30 rounded-full animate-ping" style={{ animationDuration: '2s' }} />
                <div className="absolute inset-0 -m-16 border border-purple-500/20 rounded-full" />
                <div className="absolute inset-0 -m-24 border border-purple-500/10 rounded-full" />
              </div>

              {/* User pins */}
              {[
                { top: '25%', left: '30%' },
                { top: '35%', left: '70%' },
                { top: '65%', left: '25%' },
                { top: '70%', left: '75%' },
                { top: '20%', left: '55%' },
              ].map((pos, i) => (
                <div
                  key={i}
                  ref={(el) => (pinsRef.current[i] = el)}
                  className="absolute w-10 h-10 -translate-x-1/2 -translate-y-1/2"
                  style={{ top: pos.top, left: pos.left }}
                >
                  <div className="w-full h-full rounded-full bg-white/90 border-2 border-purple-400 flex items-center justify-center overflow-hidden">
                    <span className="text-purple-600 text-xs font-bold">{i + 1}</span>
                  </div>
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-purple-400 rotate-45" />
                </div>
              ))}
            </div>
          </div>

          {/* Distance badge */}
          <div className="absolute bottom-4 right-4 px-4 py-2 bg-purple-500/20 rounded-full border border-purple-500/30">
            <span className="text-purple-300 text-sm">5 people within 5km</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LocationSection;
