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
                Luveloop helps you connect with people who share your values and intentions. 
                <span className="font-semibold text-[#0F172A]">Real conversations, genuine bonds</span> — 
                all in a calm, welcoming space.
              </p>
              
              <p className="text-lg text-gray-600 leading-relaxed">
                Whether you're looking for love, friendship, or someone who gets you, 
                we make it easy to find your people. <span className="font-medium">No pressure. No noise.</span>
              </p>
              
              <div className="bg-[#E9D5FF]/30 border-l-4 border-[#0F172A] p-6 rounded-r-lg">
                <p className="text-base text-gray-700 leading-relaxed mb-3">
                  We focus on <span className="font-semibold text-[#0F172A]">quality over quantity</span>. 
                  Every feature is designed to help you build meaningful relationships, not collect matches.
                </p>
                <p className="text-base text-[#0F172A] font-semibold">
                  Start slow. Talk honestly. Build something real.
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
                <Users size={20} className="text-[#0F172A]" />
                <span className="text-sm text-gray-600 font-medium">Real People</span>
              </div>
            </div>
          </div>
          
          {/* Right content - Single hero image */}
          <div className="relative h-[500px] lg:h-[600px] hidden lg:block">
            <div className="absolute inset-0 flex items-center justify-center">
              <img 
                src="https://customer-assets.emergentagent.com/job_datebond/artifacts/zn3pqli0_Gemini_Generated_Image_ttgcrgttgcrgttgc.png" 
                alt="Luveloop - Connect with real people" 
                className="max-w-full max-h-full object-contain rounded-3xl shadow-2xl"
              />
            </div>
            
            {/* Floating stats card */}
            <div className="absolute bottom-8 right-0 bg-white rounded-2xl p-4 shadow-xl animate-float">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-[#E9D5FF] rounded-full flex items-center justify-center">
                  <Users size={20} className="text-[#0F172A]" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-[#0F172A]">10K+</p>
                  <p className="text-xs text-gray-500">Active Users</p>
                </div>
              </div>
            </div>
            
            {/* Floating match card */}
            <div className="absolute top-1/3 left-0 bg-white rounded-2xl p-4 shadow-xl animate-float-delay-1">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-[#DBEAFE] rounded-full flex items-center justify-center">
                  <Heart size={20} className="text-[#0F172A]" fill="currentColor" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#0F172A]">New connection!</p>
                  <p className="text-xs text-gray-500">Say hello</p>
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
