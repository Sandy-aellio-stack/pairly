import { Heart, ArrowRight, Shield, Lock, Users, Sparkles } from 'lucide-react';

const HeroSection = ({ onGetStarted, onWaitlist }) => {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden"
    >
      {/* Romantic gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#E8D5E7] via-[#F5E6E8] to-[#FDE8D7]" />
      
      {/* Decorative shapes */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-[#FFD4D4]/30 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-10 w-80 h-80 bg-[#D4E5FF]/30 rounded-full blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#FFE4D4]/20 rounded-full blur-3xl" />
      
      <div className="container mx-auto px-6 py-16 relative z-10 pt-24">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left content */}
          <div className="text-center lg:text-left space-y-6 hero-content">
            <div className="hero-badge inline-flex items-center space-x-2 px-5 py-2.5 bg-white/80 backdrop-blur-sm rounded-full shadow-lg">
              <Sparkles size={18} className="text-pink-500" />
              <span className="text-sm font-semibold text-[#0F172A]">Find your perfect match</span>
            </div>
            
            <h1 className="hero-title text-5xl md:text-6xl lg:text-7xl font-bold text-[#0F172A] leading-tight">
              Meet New People.
              <br />
              <span className="bg-gradient-to-r from-pink-500 via-rose-500 to-orange-400 bg-clip-text text-transparent">
                Make Real Connections.
              </span>
            </h1>
            
            <div className="hero-subtitle space-y-4">
              <p className="text-xl text-gray-700 leading-relaxed">
                Luveloop helps you connect with people who share your values and intentions. 
                <span className="font-semibold text-[#0F172A]"> Real conversations, genuine bonds</span> — 
                all in a calm, welcoming space.
              </p>
              
              <p className="text-lg text-gray-600 leading-relaxed">
                Whether you're looking for love, friendship, or someone who gets you, 
                we make it easy to find your people.
              </p>
            </div>
            
            <div className="hero-cta flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-4">
              <button
                onClick={onGetStarted}
                className="px-8 py-4 bg-gradient-to-r from-pink-500 to-rose-500 text-white rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2 group"
              >
                <span>Get Started Free</span>
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button
                onClick={onWaitlist}
                className="hero-cta px-8 py-4 bg-white/80 backdrop-blur-sm text-[#0F172A] border-2 border-white rounded-full font-semibold hover:bg-white hover:shadow-lg transition-all duration-300"
              >
                Join Waitlist
              </button>
            </div>
            
            <div className="hero-cta flex items-center justify-center lg:justify-start space-x-6 pt-4">
              <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full">
                <Shield size={18} className="text-green-600" />
                <span className="text-sm text-gray-700 font-medium">Verified Profiles</span>
              </div>
              <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full">
                <Lock size={18} className="text-green-600" />
                <span className="text-sm text-gray-700 font-medium">Secure & Private</span>
              </div>
            </div>
          </div>
          
          {/* Right content - Hero image with the romantic style */}
          <div className="relative h-[500px] lg:h-[600px] flex items-center justify-center">
            <div className="relative">
              {/* Main illustration image */}
              <img 
                src="https://customer-assets.emergentagent.com/job_truebond-notify/artifacts/8q937866_Gemini_Generated_Image_c05duoc05duoc05d.png" 
                alt="Luveloop - Connect with real people" 
                className="w-full max-w-lg object-contain drop-shadow-2xl rounded-3xl"
              />
              
              {/* Floating stats card */}
              <div className="absolute -bottom-4 -right-4 bg-white rounded-2xl p-4 shadow-xl animate-bounce-slow">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-pink-400 to-rose-500 rounded-full flex items-center justify-center">
                    <Users size={20} className="text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-[#0F172A]">10K+</p>
                    <p className="text-xs text-gray-500">Active Users</p>
                  </div>
                </div>
              </div>
              
              {/* Floating match card */}
              <div className="absolute top-10 -left-4 bg-white rounded-2xl p-4 shadow-xl animate-float">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-rose-400 to-pink-500 rounded-full flex items-center justify-center">
                    <Heart size={20} className="text-white" fill="currentColor" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#0F172A]">New connection!</p>
                    <p className="text-xs text-gray-500">Say hello 👋</p>
                  </div>
                </div>
              </div>
              
              {/* Floating hearts */}
              <div className="absolute top-1/4 right-0 animate-pulse">
                <Heart size={24} className="text-pink-400" fill="currentColor" />
              </div>
              <div className="absolute bottom-1/4 left-0 animate-pulse delay-300">
                <Heart size={18} className="text-rose-400" fill="currentColor" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
        .delay-300 {
          animation-delay: 300ms;
        }
      `}</style>
    </section>
  );
};

export default HeroSection;
