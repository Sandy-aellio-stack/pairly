import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { UserPlus, Coins, MessageCircle, CreditCard } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const steps = [
  {
    icon: UserPlus,
    title: 'Sign Up',
    description: 'Create your profile in seconds. Add photos and tell us about yourself.',
    color: 'from-purple-500 to-purple-600',
  },
  {
    icon: Coins,
    title: 'Get 10 Free Coins',
    description: 'Start with 10 free coins to begin your journey of discovery.',
    color: 'from-purple-600 to-pink-500',
  },
  {
    icon: MessageCircle,
    title: 'Message Nearby People',
    description: 'Use coins to send messages. Each message costs 1 coin.',
    color: 'from-pink-500 to-purple-500',
  },
  {
    icon: CreditCard,
    title: 'Buy More When Needed',
    description: 'Purchase coins starting from just ₹100 when you run out.',
    color: 'from-purple-500 to-indigo-500',
  },
];

const HowItWorksSection = () => {
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
        gsap.from(card, {
          y: 100,
          opacity: 0,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: card,
            start: 'top 85%',
          },
          delay: i * 0.15,
        });
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="section py-32 px-6">
      <div className="max-w-7xl mx-auto">
        <div ref={titleRef} className="text-center mb-20">
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="text-xl text-white/60 max-w-2xl mx-auto">
            Getting started is simple. Follow these steps to find your bond.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, index) => (
            <div
              key={index}
              ref={(el) => (cardsRef.current[index] = el)}
              className="card-dark relative group hover:border-purple-500/30 transition-all duration-500"
            >
              {/* Step number */}
              <div className="absolute -top-4 -right-4 w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center font-bold text-lg">
                {index + 1}
              </div>

              {/* Icon */}
              <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500`}>
                <step.icon size={28} className="text-white" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold mb-3">{step.title}</h3>
              <p className="text-white/60">{step.description}</p>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gradient-to-r from-purple-500/50 to-transparent" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
