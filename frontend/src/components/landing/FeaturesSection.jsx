import { useState } from 'react';
import { Users, MessageCircle, User, Sparkles, Heart, Lock, Check } from 'lucide-react';

const features = [
  {
    id: 1,
    title: 'Intent-Based Profiles',
    description: "Users express what they're truly looking for — friendship, dating, or something deeper.",
    detailedDescription: 'Every profile starts with clear intentions, so conversations begin with mutual understanding and respect. No more guessing games or mismatched expectations.',
    Icon: Users,
    benefits: [
      'Clear communication from the start',
      'Reduced misunderstandings',
      'Better quality matches',
      'Honest relationship goals'
    ]
  },
  {
    id: 2,
    title: 'Conversation-First Experience',
    description: 'Messaging is intentional. Every message matters, encouraging meaningful dialogue.',
    detailedDescription: 'Our coin-based messaging system ensures thoughtful communication. Each message is valued, reducing spam and promoting genuine interest.',
    Icon: MessageCircle,
    benefits: [
      'Thoughtful, quality messages',
      'No mindless chatting',
      'Reduced spam and bots',
      'Meaningful conversations only'
    ]
  },
  {
    id: 3,
    title: 'Profile Depth Over Photos',
    description: 'Profiles focus on personality, values, and interests — not just images.',
    detailedDescription: 'We prioritize who you are over how you look. Rich profiles include values, interests, life goals, and personality insights to create deeper connections.',
    Icon: User,
    benefits: [
      'Showcase your true personality',
      'Connect on shared values',
      'Move beyond superficial judgments',
      'Find compatible matches'
    ]
  },
  {
    id: 4,
    title: 'Smart Matching',
    description: 'Matches are based on compatibility and intent, not just location or looks.',
    detailedDescription: 'Our intelligent algorithm considers values, interests, relationship goals, and communication styles to suggest truly compatible matches.',
    Icon: Sparkles,
    benefits: [
      'Quality over quantity',
      'Values-based matching',
      'Intent alignment',
      'Compatibility-focused'
    ]
  },
  {
    id: 5,
    title: 'Calm, Friendly UI',
    description: 'Soft colors, gentle animations, and a distraction-free experience that feels safe.',
    detailedDescription: 'Every design choice prioritizes your emotional wellbeing. No pressure loops, no endless scrolling, no anxiety-inducing features — just a peaceful space to connect.',
    Icon: Heart,
    benefits: [
      'Stress-free browsing',
      'No dark patterns',
      'Emotionally safe environment',
      'Intuitive navigation'
    ]
  },
  {
    id: 6,
    title: 'Privacy Protection',
    description: "Your data is yours. We never sell your information or show you to people you didn't match with.",
    detailedDescription: 'Bank-level encryption, transparent data practices, and complete control over your visibility. Your privacy is non-negotiable.',
    Icon: Lock,
    benefits: [
      'End-to-end encryption',
      'No data selling',
      'Control your visibility',
      'Transparent policies'
    ]
  }
];

const FeaturesSection = () => {
  const [activeFeature, setActiveFeature] = useState(0);

  return (
    <section
      id="features"
      className="relative py-28 bg-[#F8FAFC] lg:pl-20"
    >
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-4xl mx-auto mb-16 space-y-6">
          <span className="text-sm font-semibold text-[#0F172A] uppercase tracking-wider">✨ Features</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A]">
            Thoughtfully Designed Features
          </h2>
          <p className="text-xl md:text-2xl text-gray-700 leading-relaxed">
            TrueBond is thoughtfully designed with features that support real connection. 
            Every element prioritizes your wellbeing and helps foster genuine relationships.
          </p>
        </div>

        {/* Features grid */}
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
            {features.map((feature, index) => {
              const IconComponent = feature.Icon;
              return (
                <button
                  key={feature.id}
                  onClick={() => setActiveFeature(index)}
                  className={`text-left rounded-2xl p-8 transition-all duration-300 feature-card ${
                    activeFeature === index
                      ? 'bg-white border-2 border-[#0F172A] shadow-2xl scale-105'
                      : 'bg-white hover:bg-gray-50 border border-gray-200 shadow-md hover:shadow-lg'
                  }`}
                >
                  <div className="space-y-4">
                    <div
                      className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all ${
                        activeFeature === index
                          ? 'bg-[#0F172A] shadow-lg scale-110'
                          : 'bg-[#E9D5FF]'
                      }`}
                    >
                      <IconComponent
                        size={32}
                        className={activeFeature === index ? 'text-white' : 'text-[#0F172A]'}
                      />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-[#0F172A] mb-3">
                        {feature.title}
                      </h3>
                      <p className="text-gray-700 leading-relaxed mb-4">
                        {feature.description}
                      </p>
                      {activeFeature === index && (
                        <>
                          <p className="text-sm text-gray-600 italic mb-4 bg-[#F8FAFC] rounded-lg p-3">
                            {feature.detailedDescription}
                          </p>
                          <div className="space-y-2">
                            <p className="text-sm font-semibold text-[#0F172A]">Key Benefits:</p>
                            <ul className="space-y-1.5">
                              {feature.benefits.map((benefit, idx) => (
                                <li key={idx} className="flex items-start space-x-2">
                                  <Check size={16} className="text-green-600 flex-shrink-0 mt-0.5" />
                                  <span className="text-sm text-gray-700">{benefit}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Feature highlight banner */}
          <div className="bg-[#0F172A] rounded-3xl p-10 text-white shadow-2xl">
            <div className="max-w-4xl mx-auto text-center space-y-6">
              <div className="inline-flex items-center space-x-2 bg-white/20 rounded-full px-6 py-2 backdrop-blur-sm">
                <Sparkles size={20} />
                <span className="font-semibold">Featured Highlight</span>
              </div>
              <h3 className="text-3xl md:text-4xl font-bold">
                {features[activeFeature].title}
              </h3>
              <p className="text-xl text-white/90 leading-relaxed">
                {features[activeFeature].detailedDescription}
              </p>
              <div className="grid md:grid-cols-2 gap-6 pt-6">
                {features[activeFeature].benefits.map((benefit, idx) => (
                  <div key={idx} className="flex items-center space-x-3 bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                    <Check size={24} className="text-green-300 flex-shrink-0" />
                    <span className="font-medium">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
