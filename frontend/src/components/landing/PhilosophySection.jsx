import { useState } from 'react';
import { Zap, Heart, Shield, User, Target, Search, MessageCircle, Sparkles, BookOpen, MessageSquare, Ear } from 'lucide-react';

const demoSteps = [
  {
    id: 1,
    title: 'Create Your Profile',
    description: 'Share your interests, values, and what you are looking for.',
    detailedInfo: 'Our onboarding helps you express who you really are through thoughtful prompts.',
    Icon: User,
    image: 'https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=600'
  },
  {
    id: 2,
    title: 'Set Your Intentions',
    description: 'Choose friendship, dating, or something deeper.',
    detailedInfo: 'Be clear from the start so everyone is on the same page.',
    Icon: Target,
    image: 'https://images.unsplash.com/photo-1517842645767-c639042777db?w=600'
  },
  {
    id: 3,
    title: 'Find Your People',
    description: 'We suggest matches based on real compatibility.',
    detailedInfo: 'Quality over quantity. Each match is intentional.',
    Icon: Search,
    image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600'
  },
  {
    id: 4,
    title: 'Start Talking',
    description: 'Send messages that matter. No pressure.',
    detailedInfo: 'Take your time to craft thoughtful responses.',
    Icon: MessageCircle,
    image: 'https://images.unsplash.com/photo-1543269865-cbf427effbad?w=600'
  },
  {
    id: 5,
    title: 'Build a Bond',
    description: 'Let connection grow naturally, at your pace.',
    detailedInfo: 'We walk with you, not push you forward.',
    Icon: Sparkles,
    image: 'https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=600'
  }
];

const coreValues = [
  {
    title: 'Intentional Over Impulsive',
    description: 'Think before swiping. Read before judging. Connect with purpose.',
    Icon: Zap
  },
  {
    title: 'Meaningful Over Addictive',
    description: 'No dark patterns. No endless scrolling. Just genuine engagement.',
    Icon: Heart
  },
  {
    title: 'Respect Over Attention',
    description: 'Your time matters. Quality interactions over attention-grabbing tactics.',
    Icon: Shield
  }
];

const PhilosophySection = () => {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <section
      id="philosophy"
      className="relative py-28 bg-white lg:pl-20"
    >
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-4xl mx-auto mb-16 space-y-6">
          <span className="text-sm font-semibold text-[#7C3AED] uppercase tracking-wider">Our Philosophy</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A]">
            Connection Takes Time
          </h2>
          <p className="text-xl text-gray-600 leading-relaxed">
            Real bonds aren't built in a swipe. We designed Luveloop to slow things down and let relationships grow naturally.
          </p>
        </div>

        {/* Core values */}
        <div className="max-w-5xl mx-auto mb-20">
          <div className="grid md:grid-cols-3 gap-8">
            {coreValues.map((value, index) => {
              const IconComponent = value.Icon;
              return (
                <div
                  key={index}
                  className="bg-[#F8FAFC] rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-t-4 border-[#0F172A]"
                >
                  <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 bg-[#E9D5FF] rounded-full flex items-center justify-center">
                      <IconComponent size={32} className="text-[#0F172A]" />
                    </div>
                  </div>
                  <h3 className="text-xl font-bold text-[#0F172A] mb-3 text-center">{value.title}</h3>
                  <p className="text-gray-600 text-center leading-relaxed">{value.description}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* How it works section */}
        <div className="max-w-6xl mx-auto">
          <h3 className="text-3xl font-bold text-[#0F172A] text-center mb-4">
            The Journey
          </h3>
          <p className="text-lg text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            No manipulation. No pressure. Just a natural path to connection.
          </p>

          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Steps list */}
            <div className="space-y-4">
              {demoSteps.map((step, index) => {
                const IconComponent = step.Icon;
                return (
                  <button
                    key={step.id}
                    onClick={() => setActiveStep(index)}
                    className={`w-full text-left rounded-2xl p-5 transition-all duration-300 ${
                      activeStep === index
                        ? 'bg-[#E9D5FF]/50 border-2 border-[#0F172A] shadow-xl'
                        : 'bg-gray-50 hover:bg-gray-100 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start space-x-4">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                          activeStep === index ? 'bg-[#0F172A]' : 'bg-[#E9D5FF]'
                        }`}
                      >
                        <IconComponent
                          size={24}
                          className={activeStep === index ? 'text-white' : 'text-[#0F172A]'}
                        />
                      </div>
                      <div className="flex-1">
                        <span className="text-xs font-semibold text-[#7C3AED]">Step {index + 1}</span>
                        <h3 className="text-lg font-bold text-[#0F172A] mb-1">{step.title}</h3>
                        <p className="text-gray-600 text-sm">{step.description}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
            
            {/* Image showcase */}
            <div className="lg:sticky lg:top-24">
              <div className="relative h-80 md:h-[450px] bg-gray-100 rounded-3xl overflow-hidden shadow-2xl">
                <img
                  src={demoSteps[activeStep].image}
                  alt={demoSteps[activeStep].title}
                  className="w-full h-full object-cover transition-opacity duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                    <p className="text-white font-bold text-xl mb-1">{demoSteps[activeStep].title}</p>
                    <p className="text-white/90 text-sm">{demoSteps[activeStep].detailedInfo}</p>
                  </div>
                </div>
              </div>

              {/* Step indicators */}
              <div className="flex justify-center space-x-2 mt-4">
                {demoSteps.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveStep(index)}
                    className={`h-2 rounded-full transition-all duration-300 ${
                      activeStep === index ? 'bg-[#0F172A] w-8' : 'bg-gray-300 w-2'
                    }`}
                    aria-label={`View step ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PhilosophySection;
