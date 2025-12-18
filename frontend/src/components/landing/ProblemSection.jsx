import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { X, Clock, Shield, Heart } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const ProblemSection = () => {
  const sectionRef = useRef(null);
  const titleRef = useRef(null);
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
            delay: i * 0.15,
          });
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const problems = [
    {
      icon: X,
      title: 'Fake Profiles',
      description: 'Tired of wasting time on profiles that are not real? We verify every user.',
      color: 'from-red-500 to-orange-500',
      bgColor: 'bg-red-50',
      iconColor: 'text-red-600',
    },
    {
      icon: Clock,
      title: 'Endless Swiping',
      description: 'Stop mindlessly swiping. Our AI finds quality matches that truly matter.',
      color: 'from-yellow-500 to-orange-500',
      bgColor: 'bg-yellow-50',
      iconColor: 'text-yellow-600',
    },
    {
      icon: Shield,
      title: 'Privacy Concerns',
      description: 'Your data deserves protection. We never sell your information to anyone.',
      color: 'from-blue-500 to-indigo-500',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
  ];

  return (
    <section id="problem" ref={sectionRef} className="py-20 lg:py-28 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 lg:px-12">
        <div ref={titleRef} className="text-center mb-16">
          <span className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3 block">
            The Problem
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
            Dating apps have <span className="gradient-text">lost their way</span>
          </h2>
          <p className="text-lg lg:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Modern dating shouldn't feel like a chore. We're here to fix the broken experience and bring back genuine connections.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {problems.map((problem, i) => (
            <div
              key={i}
              ref={(el) => (cardsRef.current[i] = el)}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-100 hover:border-gray-200"
            >
              <div className={`w-16 h-16 rounded-2xl ${problem.bgColor} flex items-center justify-center mb-6`}>
                <problem.icon size={32} className={problem.iconColor} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">{problem.title}</h3>
              <p className="text-gray-600 leading-relaxed">{problem.description}</p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-purple-100 to-pink-100 rounded-full">
            <Heart size={20} className="text-purple-600" fill="currentColor" />
            <span className="text-gray-700 font-medium">
              That's why we built TrueBond differently
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProblemSection;
