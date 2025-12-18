import { Heart, ArrowRight, Shield, Lock, Users } from 'lucide-react';

const HeroSection = ({ onGetStarted, onWaitlist }) => {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#F8FAFC] pt-20"
    >
      <div className="container mx-auto px-6 py-16 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center lg:pl-20">
          {/* Left content */}
          <div className="text-center lg:text-left space-y-8">
            <div className="inline-flex items-center space-x-2 px-5 py-2.5 bg-[#E9D5FF] rounded-full">
              <Heart size={18} className="text-[#0F172A]" fill="currentColor" />
              <span className="text-sm font-semibold text-[#0F172A]">Join thousands building real connections</span>
            </div>
            
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-[#0F172A] leading-tight">
              Meet New People.
              <br />
              <span className="gradient-text">
                Make Real Connections.
              </span>
            </h1>
            
            <div className="space-y-6">
              <p className="text-xl md:text-2xl text-gray-700 leading-relaxed">
                TrueBond is built for people who are tired of surface-level matches and endless swiping. 
                We help you connect with <span className="font-semibold text-[#0F172A]">real humans, 
                real intentions, and real emotions</span> — all in a calm, safe, and welcoming space.
              </p>
              
              <p className="text-lg text-gray-600 leading-relaxed">
                Whether you're looking for love, meaningful friendship, or someone who truly understands you, 
                TrueBond makes connection feel natural again. <span className="font-medium">No pressure. No noise.</span> Just genuine conversations that matter.
              </p>
              
              <div className="bg-[#E9D5FF]/30 border-l-4 border-[#0F172A] p-6 rounded-r-lg">
                <p className="text-base text-gray-700 leading-relaxed mb-3">
                  We believe every connection starts with trust. That's why TrueBond focuses on{' '}
                  <span className="font-semibold text-[#0F172A]">quality over quantity</span>, 
                  thoughtful design over distraction, and human emotion over algorithms that rush decisions.
                </p>
                <p className="text-base text-[#0F172A] font-semibold">
                  💬 Start slow. Talk honestly. Build something real.
                </p>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-6">
              <button
                onClick={onGetStarted}
                className="px-8 py-4 bg-[#0F172A] text-white rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center space-x-2 group"
              >
                <span>Get Started Free</span>
                <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button
                onClick={onWaitlist}
                className="px-8 py-4 bg-white text-[#0F172A] border-2 border-[#0F172A] rounded-full font-semibold hover:bg-gray-50 hover:shadow-lg transition-all duration-300"
              >
                Join Waitlist
              </button>
            </div>
            
            <div className="flex items-center justify-center lg:justify-start space-x-8 pt-6">
              <div className="flex items-center space-x-2">
                <Shield size={20} className="text-green-600" />
                <span className="text-sm text-gray-600 font-medium">Verified Profiles</span>
              </div>
              <div className="flex items-center space-x-2">
                <Lock size={20} className="text-green-600" />
                <span className="text-sm text-gray-600 font-medium">Secure & Private</span>
              </div>
              <div className="flex items-center space-x-2">
                <Heart size={20} className="text-rose-500" fill="currentColor" />
                <span className="text-sm text-gray-600 font-medium">Real People</span>
              </div>
            </div>
          </div>
          
          {/* Right content - Blob profile images */}
          <div className="relative h-[500px] lg:h-[600px] hidden lg:block">
            {/* Profile 1 - Top Left */}
            <div className="relative w-32 h-32 md:w-40 md:h-40 absolute top-0 left-8 animate-float-slow">
              <div className="absolute inset-0 bg-blob-peach blob-shape-2 scale-110"></div>
              <img 
                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400" 
                alt="Happy user" 
                className="relative w-full h-full object-cover blob-shape-2"
              />
            </div>
            
            {/* Profile 2 - Top Right */}
            <div className="relative w-40 h-40 md:w-52 md:h-52 absolute top-20 right-0 animate-float-delay-1">
              <div className="absolute inset-0 bg-blob-blue blob-shape-3 scale-110"></div>
              <img 
                src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400" 
                alt="Happy user" 
                className="relative w-full h-full object-cover blob-shape-3"
              />
            </div>
            
            {/* Profile 3 - Bottom Center */}
            <div className="relative w-40 h-40 md:w-52 md:h-52 absolute bottom-0 left-1/4 animate-float-delay-2">
              <div className="absolute inset-0 bg-blob-purple blob-shape scale-110"></div>
              <img 
                src="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400" 
                alt="Happy user" 
                className="relative w-full h-full object-cover blob-shape"
              />
            </div>
            
            {/* Floating stats card */}
            <div className="absolute bottom-32 right-8 bg-white rounded-2xl p-4 shadow-xl animate-float">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-[#E9D5FF] rounded-full flex items-center justify-center">
                  <Users size={20} className="text-[#0F172A]" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-[#0F172A]">10K+</p>
                  <p className="text-xs text-gray-500">Daily Conversations</p>
                </div>
              </div>
            </div>
            
            {/* Floating match card */}
            <div className="absolute top-1/2 left-0 bg-white rounded-2xl p-4 shadow-xl animate-float-delay-1">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-[#FCE7F3] rounded-full flex items-center justify-center">
                  <Heart size={20} className="text-rose-500" fill="currentColor" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#0F172A]">New match!</p>
                  <p className="text-xs text-gray-500">Say hello 👋</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
