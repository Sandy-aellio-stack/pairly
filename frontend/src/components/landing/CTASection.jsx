import { Heart, ArrowRight, Check, MessageCircle, Phone, Video } from 'lucide-react';

const CTASection = ({ onGetStarted }) => {
  return (
    <section
      id="cta"
      className="relative py-28 overflow-hidden"
      style={{
        backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.7)), url('https://customer-assets.emergentagent.com/job_datebond/artifacts/urcyl3fg_WhatsApp%20Image%202025-12-15%20at%2015.05.44%20%282%29.jpeg')`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-[#E9D5FF]/10 rounded-full blur-3xl"></div>
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-[#DBEAFE]/10 rounded-full blur-3xl"></div>
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto text-center text-white space-y-8">
          <Heart size={56} className="mx-auto text-[#E9D5FF]" fill="currentColor" />
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold">
            Ready to Meet Someone Real?
          </h2>
          
          <p className="text-xl text-white/90 max-w-2xl mx-auto">
            Join TrueBond and start having conversations that actually matter.
            No games, no gimmicks—just real people looking for real connection.
          </p>
          
          {/* Coin reminder */}
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 max-w-md mx-auto">
            <p className="text-sm text-white/80 mb-3">Start with 10 free coins</p>
            <div className="flex justify-center gap-6 text-sm">
              <div className="flex items-center gap-1">
                <MessageCircle size={16} />
                <span>1 coin/msg</span>
              </div>
              <div className="flex items-center gap-1">
                <Phone size={16} />
                <span>5 coins/min</span>
              </div>
              <div className="flex items-center gap-1">
                <Video size={16} />
                <span>10 coins/min</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <button
              onClick={onGetStarted}
              className="px-8 py-4 bg-white text-[#0F172A] rounded-full font-semibold shadow-lg hover:bg-gray-100 transition-all hover:scale-105 flex items-center justify-center space-x-2 group"
            >
              <span>Get Started Free</span>
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
              <span>10 free coins to start</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
