import { useState, useEffect } from 'react';
import { Heart, ArrowRight, Check, Sparkles } from 'lucide-react';

const CTASection = ({ onGetStarted }) => {
  const [timeLeft, setTimeLeft] = useState({
    days: 7,
    hours: 12,
    minutes: 30,
    seconds: 0,
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev.seconds > 0) {
          return { ...prev, seconds: prev.seconds - 1 };
        } else if (prev.minutes > 0) {
          return { ...prev, minutes: prev.minutes - 1, seconds: 59 };
        } else if (prev.hours > 0) {
          return { ...prev, hours: prev.hours - 1, minutes: 59, seconds: 59 };
        } else if (prev.days > 0) {
          return { ...prev, days: prev.days - 1, hours: 23, minutes: 59, seconds: 59 };
        }
        return prev;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <section
      id="cta"
      className="relative py-28 bg-[#0F172A] overflow-hidden"
    >
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-[#E9D5FF]/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-[#FCE7F3]/10 rounded-full blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto text-center text-white space-y-8">
          <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white/20 rounded-full backdrop-blur-sm mb-4">
            <Sparkles size={20} />
            <span className="text-sm font-medium">Limited Time Offer</span>
          </div>
          
          <Heart size={56} className="mx-auto text-rose-400" fill="currentColor" />
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold">
            Ready to Meet Someone Real?
          </h2>
          
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Join TrueBond and experience a calmer, more meaningful way to connect.
            No pressure. No noise. Just honest conversations and real bonds.
          </p>
          
          {/* Countdown timer */}
          <div className="grid grid-cols-4 gap-4 max-w-md mx-auto py-8">
            {[
              { label: 'Days', value: timeLeft.days },
              { label: 'Hours', value: timeLeft.hours },
              { label: 'Minutes', value: timeLeft.minutes },
              { label: 'Seconds', value: timeLeft.seconds },
            ].map((item) => (
              <div key={item.label} className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
                <div className="text-3xl md:text-4xl font-bold">{item.value.toString().padStart(2, '0')}</div>
                <div className="text-sm opacity-80">{item.label}</div>
              </div>
            ))}
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <button
              onClick={onGetStarted}
              className="px-8 py-4 bg-white text-[#0F172A] rounded-full font-semibold shadow-lg hover:bg-gray-100 transition-all hover:scale-105 flex items-center justify-center space-x-2 group"
            >
              <span>Download Free App</span>
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="px-8 py-4 bg-transparent text-white border-2 border-white rounded-full font-semibold hover:bg-white/10 transition-all">
              Learn More
            </button>
          </div>
          
          <div className="flex items-center justify-center space-x-6 pt-6 text-sm opacity-80">
            <div className="flex items-center space-x-2">
              <Check size={18} />
              <span>No credit card required</span>
            </div>
            <div className="flex items-center space-x-2">
              <Check size={18} />
              <span>10 free conversation coins</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
