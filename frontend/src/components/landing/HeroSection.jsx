import { Heart, ArrowRight, Shield, Lock, Sparkles, Users, Star } from 'lucide-react';

const HeroSection = ({ onGetStarted, onWaitlist }) => {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-[#F8FAFC] via-white to-[#E9D5FF]/20"
    >
      {/* Background elements */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-10 w-72 h-72 bg-[#E9D5FF]/30 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#FCE7F3]/30 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-[#DBEAFE]/20 to-[#E9D5FF]/20 rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-6 py-20 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left space-y-8">
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white rounded-full shadow-md border border-gray-100">
              <Sparkles size={16} className="text-[#0F172A]" />
              <span className="text-sm font-medium text-[#0F172A]">Designed for genuine connections</span>
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-[#0F172A] leading-tight">
              Meet New People.
              <br />
              <span className="text-[#0F172A]">Make Real</span>{' '}
              <span className="bg-gradient-to-r from-rose-500 to-pink-500 bg-clip-text text-transparent">
                Connections.
              </span>
            </h1>

            <p className="text-xl text-gray-600 leading-relaxed max-w-xl">
              Luveloop helps you connect with people who share your values and intentions.
              <span className="font-semibold text-[#0F172A]"> Real conversations, genuine bonds</span> — 
              all in a calm, welcoming space.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <button
                onClick={onGetStarted}
                className="px-8 py-4 bg-[#0F172A] text-white rounded-full font-semibold hover:bg-gray-800 transition-all duration-300 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl"
              >
                <span>Get Started</span>
                <ArrowRight size={20} />
              </button>
              
              <button
                onClick={onWaitlist}
                className="px-8 py-4 bg-white text-[#0F172A] border-2 border-gray-200 rounded-full font-semibold hover:border-[#0F172A] transition-all duration-300"
              >
                Learn More
              </button>
            </div>

            <div className="flex items-center justify-center lg:justify-start space-x-8 pt-4">
              <div className="flex items-center space-x-2">
                <Shield size={20} className="text-green-600" />
                <span className="text-sm text-gray-600">Verified Profiles</span>
              </div>
              <div className="flex items-center space-x-2">
                <Lock size={20} className="text-green-600" />
                <span className="text-sm text-gray-600">Secure & Private</span>
              </div>
            </div>
          </div>

          {/* Right Content - App Preview */}
          <div className="relative flex items-center justify-center">
            <div className="relative">
              {/* Phone mockup */}
              <div className="w-72 h-[580px] bg-[#0F172A] rounded-[3rem] p-3 shadow-2xl">
                <div className="w-full h-full bg-white rounded-[2.5rem] overflow-hidden">
                  {/* App header */}
                  <div className="bg-gradient-to-r from-rose-500 to-pink-500 p-6 text-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Heart size={24} fill="white" />
                        <span className="font-bold text-lg">Luveloop</span>
                      </div>
                      <div className="w-10 h-10 bg-white/20 rounded-full" />
                    </div>
                    <p className="mt-4 text-white/90 text-sm">Find your perfect match</p>
                  </div>
                  
                  {/* Profile cards */}
                  <div className="p-4 space-y-3">
                    {[
                      { name: 'Priya', age: 24, distance: '2km', color: 'from-pink-400 to-rose-400' },
                      { name: 'Amit', age: 27, distance: '5km', color: 'from-purple-400 to-indigo-400' },
                      { name: 'Sara', age: 23, distance: '3km', color: 'from-orange-400 to-pink-400' },
                    ].map((profile, i) => (
                      <div key={i} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-xl">
                        <div className={`w-12 h-12 bg-gradient-to-br ${profile.color} rounded-full flex items-center justify-center text-white font-bold`}>
                          {profile.name[0]}
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-[#0F172A]">{profile.name}, {profile.age}</p>
                          <p className="text-xs text-gray-500">{profile.distance} away</p>
                        </div>
                        <Heart size={20} className="text-rose-400" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Floating cards */}
              <div className="absolute -top-4 -right-4 bg-white rounded-2xl p-4 shadow-xl animate-bounce-slow">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-rose-400 to-pink-500 rounded-full flex items-center justify-center">
                    <Heart size={16} className="text-white" fill="white" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#0F172A]">New Match!</p>
                    <p className="text-xs text-gray-500">Say hello 👋</p>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-4 -left-4 bg-white rounded-2xl p-4 shadow-xl">
                <div className="flex items-center space-x-3">
                  <div className="flex -space-x-2">
                    {[1,2,3].map(i => (
                      <div key={i} className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full border-2 border-white" />
                    ))}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#0F172A]">10K+</p>
                    <p className="text-xs text-gray-500">Active users</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        .animate-bounce-slow {
          animation: bounce-slow 3s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
};

export default HeroSection;
