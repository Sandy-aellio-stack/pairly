import { useState, useEffect } from 'react';
import { Heart, MessageCircle, MapPin, Sparkles, ChevronRight, X, Check } from 'lucide-react';
import useAuthStore from '@/store/authStore';

// Mock suggested profiles
const mockProfiles = [
  {
    id: '1',
    name: 'Priya',
    age: 26,
    bio: 'Coffee lover ☕ | Travel enthusiast ✈️ | Looking for genuine connections',
    profile_pictures: ['https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400'],
    intent: 'serious',
    distance_km: 2.5,
    interests: ['Travel', 'Photography', 'Coffee']
  },
  {
    id: '2',
    name: 'Arjun',
    age: 28,
    bio: 'Software engineer by day, musician by night 🎸',
    profile_pictures: ['https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400'],
    intent: 'dating',
    distance_km: 3.2,
    interests: ['Music', 'Tech', 'Hiking']
  },
  {
    id: '3',
    name: 'Ananya',
    age: 24,
    bio: 'Art lover 🎨 | Yoga practitioner 🧘‍♀️ | Let\'s have meaningful conversations',
    profile_pictures: ['https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400'],
    intent: 'friendship',
    distance_km: 4.1,
    interests: ['Art', 'Yoga', 'Reading']
  },
];

const HomePage = () => {
  const { user } = useAuthStore();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [profiles, setProfiles] = useState(mockProfiles);

  const currentProfile = profiles[currentIndex];

  const handleLike = () => {
    // TODO: Implement like functionality
    if (currentIndex < profiles.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePass = () => {
    if (currentIndex < profiles.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleMessage = () => {
    // TODO: Navigate to chat
  };

  return (
    <div className="max-w-6xl mx-auto px-4">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">
          Welcome back, {user?.name || 'User'}! 👋
        </h1>
        <p className="text-gray-600">Find your perfect match today</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Card Stack */}
        <div className="lg:col-span-2">
          {currentProfile ? (
            <div className="relative">
              {/* Profile Card */}
              <div className="bg-white rounded-3xl shadow-xl overflow-hidden">
                {/* Image */}
                <div className="relative h-[500px]">
                  <img
                    src={currentProfile.profile_pictures[0]}
                    alt={currentProfile.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                  
                  {/* Profile Info Overlay */}
                  <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-3xl font-bold">{currentProfile.name}, {currentProfile.age}</h2>
                      <span className="px-2 py-1 bg-white/20 rounded-full text-xs backdrop-blur-sm">
                        {currentProfile.intent}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-white/80 mb-3">
                      <MapPin size={14} />
                      <span>{currentProfile.distance_km} km away</span>
                    </div>
                    
                    <p className="text-white/90 mb-4">{currentProfile.bio}</p>
                    
                    <div className="flex flex-wrap gap-2">
                      {currentProfile.interests.map((interest, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-white/20 rounded-full text-xs backdrop-blur-sm"
                        >
                          {interest}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="p-6 flex items-center justify-center gap-4">
                  <button
                    onClick={handlePass}
                    className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
                  >
                    <X size={28} className="text-gray-500" />
                  </button>
                  
                  <button
                    onClick={handleMessage}
                    className="w-14 h-14 rounded-full bg-[#E9D5FF] flex items-center justify-center hover:bg-[#DDD6FE] transition-colors"
                  >
                    <MessageCircle size={24} className="text-[#0F172A]" />
                  </button>
                  
                  <button
                    onClick={handleLike}
                    className="w-16 h-16 rounded-full bg-rose-500 flex items-center justify-center hover:bg-rose-600 transition-colors shadow-lg"
                  >
                    <Heart size={28} className="text-white" fill="white" />
                  </button>
                </div>
              </div>

              {/* Card Stack Indicator */}
              <div className="flex justify-center gap-2 mt-4">
                {profiles.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-1.5 rounded-full transition-all ${
                      idx === currentIndex ? 'w-8 bg-[#0F172A]' : 'w-1.5 bg-gray-300'
                    }`}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-3xl shadow-xl p-12 text-center">
              <Sparkles size={48} className="text-[#E9D5FF] mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#0F172A] mb-2">You've seen everyone!</h2>
              <p className="text-gray-600">Check back later for more matches</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="bg-white rounded-2xl p-6 shadow-md">
            <h3 className="font-semibold text-[#0F172A] mb-4">Your Activity</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 bg-[#E9D5FF]/20 rounded-xl">
                <p className="text-3xl font-bold text-[#0F172A]">12</p>
                <p className="text-xs text-gray-600">Likes Received</p>
              </div>
              <div className="text-center p-4 bg-[#FCE7F3]/50 rounded-xl">
                <p className="text-3xl font-bold text-[#0F172A]">5</p>
                <p className="text-xs text-gray-600">Matches</p>
              </div>
            </div>
          </div>

          {/* Nearby Preview */}
          <div className="bg-white rounded-2xl p-6 shadow-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[#0F172A]">People Nearby</h3>
              <a href="/dashboard/nearby" className="text-sm text-[#0F172A] font-medium flex items-center gap-1">
                View All <ChevronRight size={16} />
              </a>
            </div>
            <div className="flex -space-x-3">
              {mockProfiles.slice(0, 4).map((profile, idx) => (
                <img
                  key={idx}
                  src={profile.profile_pictures[0]}
                  alt={profile.name}
                  className="w-12 h-12 rounded-full border-2 border-white object-cover"
                />
              ))}
              <div className="w-12 h-12 rounded-full bg-[#0F172A] border-2 border-white flex items-center justify-center">
                <span className="text-white text-xs font-semibold">+20</span>
              </div>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-gradient-to-br from-[#E9D5FF] to-[#FCE7F3] rounded-2xl p-6">
            <h3 className="font-semibold text-[#0F172A] mb-2">💡 Tip of the Day</h3>
            <p className="text-sm text-gray-700">
              Complete your profile to get 50% more matches! Add a bio and more photos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
