import { useState } from 'react';
import { Zap, Heart, Shield, User, Target, Search, MessageCircle, Sparkles, BookOpen, MessageSquare, Ear } from 'lucide-react';

const demoSteps = [
  {
    id: 1,
    title: 'Create Your Profile',
    description: "Tell your story honestly — your interests, values, and what you're looking for.",
    detailedInfo: 'Our thoughtful onboarding helps you express who you really are. Share your passions, beliefs, and relationship goals with carefully designed prompts that reveal your personality.',
    Icon: User,
    image: 'https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=600'
  },
  {
    id: 2,
    title: 'Set Your Intentions',
    description: 'Choose what kind of connection you want so everyone is on the same page.',
    detailedInfo: 'Be clear from the start: friendship, casual dating, or serious relationship. This transparency helps both parties understand expectations and creates meaningful matches.',
    Icon: Target,
    image: 'https://images.unsplash.com/photo-1517842645767-c639042777db?w=600'
  },
  {
    id: 3,
    title: 'Discover Compatible People',
    description: 'We suggest matches thoughtfully, prioritizing quality over volume.',
    detailedInfo: "Our intelligent matching considers your values, interests, and intentions — not just location. Each suggestion is intentional and based on real compatibility factors.",
    Icon: Search,
    image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600'
  },
  {
    id: 4,
    title: 'Start a Conversation',
    description: 'Each message is meaningful. No pressure, no rush.',
    detailedInfo: 'Our conversation-first approach encourages thoughtful dialogue. Take your time to craft responses that reflect your personality and show genuine interest.',
    Icon: MessageCircle,
    image: 'https://images.unsplash.com/photo-1543269865-cbf427effbad?w=600'
  },
  {
    id: 5,
    title: 'Build a Bond',
    description: 'Let the connection grow naturally, at your pace.',
    detailedInfo: "TrueBond doesn't push you forward — we walk with you. Build trust, share stories, and develop genuine connection without artificial time pressures.",
    Icon: Sparkles,
    image: 'https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=600'
  }
];

const coreValues = [
  {
    title: 'Intentional Over Impulsive',
    description: 'Every action is thoughtful. We encourage you to think before swiping, read before judging, and connect with purpose.',
    Icon: Zap
  },
  {
    title: 'Meaningful Over Addictive',
    description: 'No dark patterns or endless scrolling. Our design promotes genuine engagement, not mindless consumption.',
    Icon: Heart
  },
  {
    title: 'Respect Over Attention',
    description: 'Your time and emotional energy matter. We value quality interactions over attention-grabbing tactics.',
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
          <span className="text-sm font-semibold text-[#0F172A] uppercase tracking-wider">💭 Our Philosophy</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A]">
            Connection is Built, Not Rushed
          </h2>
          <p className="text-xl md:text-2xl text-gray-700 leading-relaxed">
            At TrueBond, we believe connection is built, not rushed. Our philosophy is simple but powerful.
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
            How It Works
          </h3>
          <p className="text-lg text-gray-600 text-center mb-12 max-w-2xl mx-auto">
            We design every interaction to slow things down and help users communicate with clarity and honesty. 
            No manipulation. No pressure loops. No emotional fatigue.
          </p>

          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Steps list */}
            <div className="space-y-6">
              {demoSteps.map((step, index) => {
                const IconComponent = step.Icon;
                return (
                  <button
                    key={step.id}
                    onClick={() => setActiveStep(index)}
                    className={`w-full text-left rounded-2xl p-6 transition-all duration-300 ${
                      activeStep === index
                        ? 'bg-[#E9D5FF]/50 border-2 border-[#0F172A] shadow-xl scale-105'
                        : 'bg-gray-50 hover:bg-gray-100 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start space-x-4">
                      <div
                        className={`w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                          activeStep === index ? 'bg-[#0F172A] scale-110' : 'bg-[#E9D5FF]'
                        }`}
                      >
                        <IconComponent
                          size={28}
                          className={activeStep === index ? 'text-white' : 'text-[#0F172A]'}
                        />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-semibold text-[#0F172A]">Step {index + 1}</span>
                        </div>
                        <h3 className="text-xl font-bold text-[#0F172A] mb-2">{step.title}</h3>
                        <p className="text-gray-700 mb-3">{step.description}</p>
                        {activeStep === index && (
                          <p className="text-sm text-gray-600 bg-white rounded-lg p-3 border-l-2 border-[#0F172A]">
                            {step.detailedInfo}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
            
            {/* Image showcase */}
            <div className="lg:sticky lg:top-24">
              <div className="relative h-96 md:h-[550px] bg-gray-100 rounded-3xl overflow-hidden shadow-2xl">
                <img
                  src={demoSteps[activeStep].image}
                  alt={demoSteps[activeStep].title}
                  className="w-full h-full object-cover transition-opacity duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
                <div className="absolute bottom-0 left-0 right-0 p-8">
                  <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
                    <p className="text-white font-bold text-2xl mb-2">{demoSteps[activeStep].title}</p>
                    <p className="text-white/90 text-sm">{demoSteps[activeStep].description}</p>
                  </div>
                </div>
              </div>

              {/* Step indicators */}
              <div className="flex justify-center space-x-2 mt-6">
                {demoSteps.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveStep(index)}
                    className={`h-2 rounded-full transition-all duration-300 ${
                      activeStep === index ? 'bg-[#0F172A] w-12' : 'bg-gray-300 w-2'
                    }`}
                    aria-label={`View step ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom encouragement */}
        <div className="max-w-3xl mx-auto mt-20 text-center space-y-4">
          <div className="bg-[#E9D5FF]/30 rounded-2xl p-8 border border-[#E9D5FF]">
            <p className="text-2xl font-bold text-[#0F172A] mb-4">
              TrueBond encourages you to:
            </p>
            <div className="grid md:grid-cols-3 gap-6 text-left">
              <div className="flex items-start space-x-3">
                <BookOpen size={24} className="text-[#0F172A] flex-shrink-0 mt-1" />
                <div>
                  <p className="font-semibold text-[#0F172A]">Read Before Reacting</p>
                  <p className="text-sm text-gray-600">Take time to understand profiles deeply</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <MessageSquare size={24} className="text-[#0F172A] flex-shrink-0 mt-1" />
                <div>
                  <p className="font-semibold text-[#0F172A]">Talk Before Judging</p>
                  <p className="text-sm text-gray-600">Give conversations a genuine chance</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Ear size={24} className="text-[#0F172A] flex-shrink-0 mt-1" />
                <div>
                  <p className="font-semibold text-[#0F172A]">Listen Before Deciding</p>
                  <p className="text-sm text-gray-600">Value their perspective and story</p>
                </div>
              </div>
            </div>
          </div>
          <p className="text-xl text-gray-700 font-medium italic">
            Because real bonds take time — and that time should feel safe, calm, and valued.
          </p>
        </div>
      </div>
    </section>
  );
};

export default PhilosophySection;
