import { useState, useEffect } from 'react';
import { Frown, Clock, UserMinus, Flame, AlertTriangle, Zap, ShieldX, ThumbsDown, VolumeX } from 'lucide-react';

const statistics = [
  { 
    percentage: '73%', 
    label: 'Report swipe fatigue',
    description: 'Users feel emotionally drained from endless superficial interactions',
    Icon: Frown
  },
  { 
    percentage: '4 min', 
    label: 'Average conversation length',
    description: 'Most chats die out before any real connection forms',
    Icon: Clock
  },
  { 
    percentage: '89%', 
    label: 'Never meet in person',
    description: 'Digital connections rarely translate to meaningful real-world relationships',
    Icon: UserMinus
  },
];

const commonProblems = [
  {
    title: 'Emotional Burnout',
    description: 'Constant swiping and rejection creates anxiety and decision fatigue',
    Icon: Flame
  },
  {
    title: 'Fake Profiles',
    description: 'Unclear intentions and catfishing make trust nearly impossible',
    Icon: AlertTriangle
  },
  {
    title: 'Pressure to Respond',
    description: 'Instant messaging expectations create unnecessary stress',
    Icon: Zap
  },
  {
    title: 'Unsafe Interactions',
    description: 'Lack of proper verification leads to uncomfortable encounters',
    Icon: ShieldX
  },
  {
    title: 'Meaningless Matches',
    description: 'High match counts but very few genuine conversations',
    Icon: ThumbsDown
  },
  {
    title: 'Lost in the Noise',
    description: 'Genuine people get buried under superficial profiles',
    Icon: VolumeX
  }
];

const ProblemSection = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % statistics.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section
      id="problem"
      className="relative py-28 bg-[#F8FAFC] overflow-hidden lg:pl-20"
    >
      <div className="container mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-4xl mx-auto space-y-6 mb-16">
          <span className="text-sm font-semibold text-[#DC2626] uppercase tracking-wider">The Problem</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A]">
            Modern Dating Apps Are Broken
          </h2>
          <p className="text-xl text-gray-700 leading-relaxed">
            Endless swiping, shallow judgments, and instant decisions based on photos alone. 
            Conversations feel disposable. Matches feel meaningless.
          </p>
          <p className="text-lg text-gray-600">
            Dating should feel <span className="font-semibold text-[#0F172A]">human</span>, not like a game.
          </p>
        </div>
        
        {/* Statistics carousel */}
        <div className="max-w-5xl mx-auto mb-20">
          <div className="grid md:grid-cols-3 gap-8">
            {statistics.map((stat, index) => {
              const IconComponent = stat.Icon;
              return (
                <div
                  key={index}
                  className={`bg-white rounded-2xl p-8 shadow-lg transition-all duration-500 hover:shadow-xl ${
                    activeIndex === index ? 'scale-105 shadow-2xl border-2 border-[#7C3AED] ring-4 ring-[#E9D5FF]' : ''
                  }`}
                >
                  <div className="flex justify-center mb-4">
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                      activeIndex === index ? 'bg-[#E9D5FF] scale-110' : 'bg-gray-100'
                    }`}>
                      <IconComponent
                        size={36}
                        className={activeIndex === index ? 'text-[#7C3AED]' : 'text-gray-400'}
                      />
                    </div>
                  </div>
                  <div className="text-5xl font-bold text-[#7C3AED] mb-3 text-center">{stat.percentage}</div>
                  <p className="text-gray-800 font-semibold text-center mb-2">{stat.label}</p>
                  <p className="text-sm text-gray-600 text-center">{stat.description}</p>
                </div>
              );
            })}n          </div>
          
          <div className="flex justify-center space-x-3 mt-8">
            {statistics.map((_, index) => (
              <button
                key={index}
                onClick={() => setActiveIndex(index)}
                className={`h-2.5 rounded-full transition-all duration-300 ${
                  activeIndex === index ? 'bg-[#7C3AED] w-12' : 'bg-gray-300 w-2.5'
                }`}
                aria-label={`View statistic ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Common problems grid */}
        <div className="max-w-6xl mx-auto">
          <h3 className="text-3xl font-bold text-[#0F172A] text-center mb-12">
            Sound Familiar?
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {commonProblems.map((problem, index) => {
              const IconComponent = problem.Icon;
              return (
                <div 
                  key={index}
                  className="bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100"
                >
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <IconComponent size={24} className="text-orange-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold text-[#0F172A] mb-2">{problem.title}</h4>
                      <p className="text-sm text-gray-600 leading-relaxed">{problem.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom message */}
        <div className="max-w-3xl mx-auto mt-16 text-center">
          <p className="text-xl text-gray-700 font-medium">
            The problem isn&apos;t people — it&apos;s how platforms are designed.
          </p>
          <p className="text-lg text-[#0F172A] font-semibold mt-4">
            There&apos;s a better way.
          </p>
        </div>
      </div>
    </section>
  );
};

export default ProblemSection;
