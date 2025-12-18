import { useState } from 'react';
import { UserPlus, Sparkles, MessageCircle, Heart, Users, Clock, Check } from 'lucide-react';

const steps = [
  {
    id: 1,
    title: 'Create Your Profile',
    description: "Answer thoughtful questions about your values, interests, and what you're looking for in a connection.",
    timeframe: '10-15 minutes',
    successRate: '95% completion rate',
    Icon: UserPlus,
  },
  {
    id: 2,
    title: 'Get Matched',
    description: 'Our algorithm finds compatible people based on your answers, not just your photos.',
    timeframe: 'Instant',
    successRate: '87% match satisfaction',
    Icon: Sparkles,
  },
  {
    id: 3,
    title: 'Start Conversations',
    description: 'Begin with conversation starters tailored to your shared interests and values.',
    timeframe: 'Within 24 hours',
    successRate: '73% response rate',
    Icon: MessageCircle,
  },
  {
    id: 4,
    title: 'Build Connection',
    description: 'Take your time getting to know each other through meaningful dialogue.',
    timeframe: '1-2 weeks',
    successRate: '18 min avg conversation',
    Icon: Heart,
  },
  {
    id: 5,
    title: 'Meet in Person',
    description: "When you're both ready, take your connection offline and meet face-to-face.",
    timeframe: 'Your timeline',
    successRate: '67% meeting rate',
    Icon: Users,
  },
];

const HowItWorksSection = () => {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <section id="how-it-works" className="py-28 bg-white lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-sm font-semibold text-[#0F172A] uppercase tracking-wider">🔄 How It Works</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            Five Simple Steps
          </h2>
          <p className="text-xl text-gray-600">
            TrueBond doesn't push you forward — it walks with you.
          </p>
        </div>
        
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <div className="absolute left-8 top-8 bottom-8 w-0.5 bg-[#E9D5FF] hidden md:block"></div>
            
            {steps.map((step, index) => {
              const IconComponent = step.Icon;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(index)}
                  className={`w-full flex items-start mb-8 last:mb-0 text-left transition-all ${
                    activeStep === index ? 'scale-105' : ''
                  }`}
                >
                  <div className={`flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center transition-all z-10 ${
                    activeStep === index
                      ? 'bg-[#0F172A] shadow-lg'
                      : 'bg-[#E9D5FF]'
                  }`}>
                    <IconComponent
                      size={28}
                      className={activeStep === index ? 'text-white' : 'text-[#0F172A]'}
                    />
                  </div>
                  
                  <div className={`ml-6 flex-1 rounded-2xl p-6 transition-all ${
                    activeStep === index
                      ? 'bg-[#E9D5FF]/50 border-2 border-[#0F172A] shadow-lg'
                      : 'bg-gray-50'
                  }`}>
                    <h3 className="text-2xl font-semibold text-[#0F172A] mb-2">{step.title}</h3>
                    <p className="text-gray-600 mb-4">{step.description}</p>
                    <div className="flex flex-wrap gap-4">
                      <span className="px-3 py-1 bg-white text-[#0F172A] rounded-full text-sm font-medium border border-[#E9D5FF] inline-flex items-center">
                        <Clock size={14} className="mr-1" />
                        {step.timeframe}
                      </span>
                      <span className="px-3 py-1 bg-white text-green-700 rounded-full text-sm font-medium border border-green-200 inline-flex items-center">
                        <Check size={14} className="mr-1" />
                        {step.successRate}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
