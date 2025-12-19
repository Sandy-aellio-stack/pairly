import { useState } from 'react';
import { Users, MessageCircle, User, Sparkles, Heart, Lock, Check } from 'lucide-react';

const features = [
  {
    id: 1,
    title: 'Know What You Want',
    description: 'Tell us if you want friendship, dating, or something deeper. We match you with people who want the same.',
    Icon: Users,
  },
  {
    id: 2,
    title: 'Messages That Matter',
    description: 'Our coin system keeps conversations meaningful. No spam, no bots—just real people talking.',
    Icon: MessageCircle,
  },
  {
    id: 3,
    title: 'More Than Photos',
    description: 'Your profile shows who you are—your interests, values, and personality. Not just selfies.',
    Icon: User,
  },
  {
    id: 4,
    title: 'Better Matches',
    description: 'We look at compatibility and shared goals, not just proximity or appearance.',
    Icon: Sparkles,
  },
  {
    id: 5,
    title: 'Feels Like Home',
    description: 'Soft colors, simple design, no pressure tactics. Just a peaceful place to connect.',
    Icon: Heart,
  },
  {
    id: 6,
    title: 'Your Privacy, Protected',
    description: 'Your data stays yours. We never sell it or show your profile to people you haven\'t matched with.',
    Icon: Lock,
  }
];

const FeaturesSection = () => {
  const [activeFeature, setActiveFeature] = useState(1);

  return (
    <section
      id="features"
      className="relative py-28 bg-[#F8FAFC] lg:pl-20"
    >
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-4xl mx-auto mb-16 space-y-6">
          <span className="text-sm font-semibold text-[#7C3AED] uppercase tracking-wider">Features</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A]">
            Built for Real Connection
          </h2>
          <p className="text-xl text-gray-600 leading-relaxed">
            Everything we build is designed to help you find and keep meaningful relationships.
          </p>
        </div>

        {/* Features grid */}
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => {
              const IconComponent = feature.Icon;
              const isActive = activeFeature === feature.id;
              return (
                <button
                  key={feature.id}
                  onClick={() => setActiveFeature(feature.id)}
                  className={`text-left rounded-2xl p-6 transition-all duration-300 ${
                    isActive
                      ? 'bg-white border-2 border-[#0F172A] shadow-xl'
                      : 'bg-white hover:bg-gray-50 border border-gray-200 shadow-sm hover:shadow-md'
                  }`}
                >
                  <div className="space-y-4">
                    <div
                      className={`w-14 h-14 rounded-xl flex items-center justify-center transition-all ${
                        isActive
                          ? 'bg-[#0F172A] shadow-lg'
                          : 'bg-[#E9D5FF]'
                      }`}
                    >
                      <IconComponent
                        size={26}
                        className={isActive ? 'text-white' : 'text-[#0F172A]'}
                      />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-[#0F172A] mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed text-sm">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Feature highlight banner */}
          <div className="mt-12 bg-[#0F172A] rounded-3xl p-8 text-white shadow-xl">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <h3 className="text-2xl md:text-3xl font-bold">
                {features[activeFeature - 1].title}
              </h3>
              <p className="text-lg text-white/90 leading-relaxed">
                {features[activeFeature - 1].description}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
