import { useState } from 'react';
import { UserPlus, Sparkles, MessageCircle, Heart, Users, Clock, Check } from 'lucide-react';

const steps = [
  {
    id: 1,
    title: 'Create Your Profile',
    description: 'Tell us about yourself—your interests, values, and what kind of connection you are looking for.',
    timeframe: '10-15 min',
    Icon: UserPlus,
  },
  {
    id: 2,
    title: 'Get Matched',
    description: 'We find people who share your interests and relationship goals.',
    timeframe: 'Instant',
    Icon: Sparkles,
  },
  {
    id: 3,
    title: 'Start Talking',
    description: 'Send a message to someone who caught your attention. Quality over quantity.',
    timeframe: 'Same day',
    Icon: MessageCircle,
  },
  {
    id: 4,
    title: 'Build Connection',
    description: 'Take your time getting to know each other through real conversations.',
    timeframe: '1-2 weeks',
    Icon: Heart,
  },
  {
    id: 5,
    title: 'Meet Up',
    description: 'When you are both ready, take it offline and meet in person.',
    timeframe: 'Your pace',
    Icon: Users,
  },
];

const HowItWorksSection = () => {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <section id="how-it-works" className="py-28 bg-white lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-sm font-semibold text-[#7C3AED] uppercase tracking-wider">How It Works</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            Five Simple Steps
          </h2>
          <p className="text-xl text-gray-600">
            No pressure, no rush—just a natural path to connection.
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
                  className={`w-full flex items-start mb-6 last:mb-0 text-left transition-all ${
                    activeStep === index ? 'scale-[1.02]' : ''
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
                    <h3 className="text-xl font-semibold text-[#0F172A] mb-2">{step.title}</h3>
                    <p className="text-gray-600 mb-3">{step.description}</p>
                    <span className="px-3 py-1 bg-white text-[#0F172A] rounded-full text-sm font-medium border border-[#E9D5FF] inline-flex items-center">
                      <Clock size={14} className="mr-1" />
                      {step.timeframe}
                    </span>
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
