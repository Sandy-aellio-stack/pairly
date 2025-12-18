import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Heart, Users, Sparkles, Target } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const PhilosophySection = () => {
  const sectionRef = useRef(null);
  const titleRef = useRef(null);
  const contentRef = useRef(null);
  const cardsRef = useRef([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Title animation
      gsap.from(titleRef.current, {
        y: 50,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: titleRef.current,
          start: 'top 80%',
        },
      });

      // Content animation
      gsap.from(contentRef.current, {
        y: 40,
        opacity: 0,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: contentRef.current,
          start: 'top 80%',
        },
        delay: 0.2,
      });

      // Cards stagger animation
      cardsRef.current.forEach((card, i) => {
        if (card) {
          gsap.from(card, {
            y: 60,
            opacity: 0,
            duration: 0.8,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: card,
              start: 'top 85%',
            },
            delay: i * 0.1,
          });
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const values = [
    {
      icon: Heart,
      title: 'Authenticity First',
      description: 'Real profiles, real people, real connections. No bots, no catfishing.',
    },
    {
      icon: Users,
      title: 'Quality Over Quantity',
      description: 'Smart matching that focuses on compatibility, not endless swiping.',
    },
    {
      icon: Sparkles,
      title: 'Privacy & Safety',
      description: 'Your data is yours. We protect it like our own.',
    },
    {
      icon: Target,
      title: 'Meaningful Matches',
      description: 'We help you find relationships that matter, not just another match.',
    },
  ];

  return (
    <section id="philosophy" ref={sectionRef} className="py-20 lg:py-28 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-pink-50" />
      <div className="absolute top-[20%] right-[10%] w-[400px] h-[400px] rounded-full bg-purple-200/20 blur-[100px]" />
      <div className="absolute bottom-[10%] left-[15%] w-[350px] h-[350px] rounded-full bg-pink-200/20 blur-[100px]" />

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
        <div ref={titleRef} className="text-center mb-12">
          <span className="text-sm font-medium text-purple-600 uppercase tracking-wide mb-3 block">
            Our Philosophy
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
            Building <span className="gradient-text">real relationships</span>
            <br />
            through technology
          </h2>
          <p ref={contentRef} className="text-lg lg:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            We believe dating apps should bring people together, not keep them scrolling forever. 
            Our mission is to create meaningful connections that last beyond the first swipe.
          </p>
        </div>

        {/* Values Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
          {values.map((value, i) => (
            <div
              key={i}
              ref={(el) => (cardsRef.current[i] = el)}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-purple-200 hover:-translate-y-1"
            >
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-5">
                <value.icon size={26} className="text-white" strokeWidth={2} />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{value.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{value.description}</p>
            </div>
          ))}
        </div>

        {/* Quote/Mission Statement */}
        <div className="mt-16 max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl p-8 md:p-12 text-center text-white shadow-2xl">
            <blockquote className="text-xl md:text-2xl lg:text-3xl font-bold leading-relaxed mb-4">
              "Every great love story starts with a genuine connection. We're here to help you find yours."
            </blockquote>
            <p className="text-white/80 text-lg">— The TrueBond Team</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PhilosophySection;
