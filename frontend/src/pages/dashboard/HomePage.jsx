import { useState, useEffect } from 'react';
import { Heart, MessageCircle, MapPin, Sparkles, ChevronRight, X, Loader2, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { locationAPI, userAPI } from '@/services/api';
import { toast } from 'sonner';

const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [profiles, setProfiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // Fetch user feed on load
  useEffect(() => {
    const fetchUserFeed = async () => {
      setIsLoading(true);
      try {
        // First try to get location
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              const { latitude, longitude } = position.coords;
              setUserLocation({ lat: latitude, lng: longitude });
              
              // Update user location in backend
              try {
                await locationAPI.update(latitude, longitude);
              } catch (e) {
                console.log('Could not update location');
              }
            },
            () => {
              setUserLocation({ lat: 12.9716, lng: 77.5946 });
            }
          );
        }

        // Fetch user feed (not location-dependent)
        const response = await userAPI.getFeed(1, 20);
        if (response.data.users && response.data.users.length > 0) {
          setProfiles(response.data.users);
          setHasMore(response.data.has_more);
        } else {
          setProfiles([]);
        }
      } catch (error) {
        console.error('Failed to fetch feed:', error);
        setProfiles([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserFeed();
  }, []);

  // Search users
  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await userAPI.search(query, 1, 10);
      setSearchResults(response.data.users || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Load more users
  const loadMore = async () => {
    if (!hasMore) return;
    
    try {
      const response = await userAPI.getFeed(page + 1, 20);
      if (response.data.users && response.data.users.length > 0) {
        setProfiles([...profiles, ...response.data.users]);
        setPage(page + 1);
        setHasMore(response.data.has_more);
      }
    } catch (error) {
      console.error('Failed to load more:', error);
    }
  };

  const currentProfile = profiles[currentIndex];

  const handleLike = () => {
    toast.success(`You liked ${currentProfile?.name}!`);
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
    if (user?.credits_balance > 0) {
      navigate('/dashboard/chat');
    } else {
      toast.error('You need coins to send messages!');
      navigate('/dashboard/credits');
    }
  };

  const handleViewProfile = (profileId) => {
    navigate(`/dashboard/profile/${profileId}`);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-[#0F172A] mx-auto mb-4" />
          <p className="text-gray-600">Loading profiles...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4">
      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search users by name..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0F172A]/20"
          />
          {isSearching && (
            <Loader2 className="absolute right-4 top-1/2 transform -translate-y-1/2 w-5 h-5 animate-spin text-gray-400" />
          )}
        </div>
        
        {/* Search Results Dropdown */}
        {searchQuery && searchResults.length > 0 && (
          <div className="absolute z-50 mt-2 w-full max-w-md bg-white rounded-xl shadow-lg border border-gray-200 max-h-80 overflow-y-auto">
            {searchResults.map((result) => (
              <div
                key={result.id}
                onClick={() => handleViewProfile(result.id)}
                className="flex items-center gap-3 p-3 hover:bg-gray-50 cursor-pointer"
              >
                <img
                  src={result.profile_pictures?.[0] || 'https://via.placeholder.com/40'}
                  alt={result.name}
                  className="w-10 h-10 rounded-full object-cover"
                />
                <div>
                  <p className="font-medium text-[#0F172A]">{result.name}, {result.age}</p>
                  <p className="text-sm text-gray-500">{result.bio?.slice(0, 50) || 'No bio'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {searchQuery && searchResults.length === 0 && !isSearching && (
          <div className="absolute z-50 mt-2 w-full max-w-md bg-white rounded-xl shadow-lg border border-gray-200 p-4 text-center text-gray-500">
            No users found matching "{searchQuery}"
          </div>
        )}
      </div>

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
                {/* Image - Click to view profile */}
                <div 
                  className="relative h-[500px] cursor-pointer"
                  onClick={() => navigate(`/dashboard/profile/${currentProfile.id}`)}
                >
                  <img
                    src={currentProfile.profile_pictures?.[0] || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400'}
                    alt={currentProfile.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                  
                  {/* Tap to view indicator */}
                  <div className="absolute top-4 right-4 px-3 py-1.5 bg-black/30 backdrop-blur-sm rounded-full text-white text-xs">
                    Tap to view profile
                  </div>
                  
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
                      <span>{currentProfile.distance_display || `${currentProfile.distance_km?.toFixed(1) || '?'} km away`}</span>
                    </div>
                    
                    <p className="text-white/90 mb-4">{currentProfile.bio || 'No bio yet'}</p>
                    
                    {currentProfile.interests && (
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
                    )}
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
              <h2 className="text-2xl font-bold text-[#0F172A] mb-2">You&apos;ve seen everyone!</h2>
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
                <p className="text-3xl font-bold text-[#0F172A]">{user?.credits_balance || 10}</p>
                <p className="text-xs text-gray-600">Coins Left</p>
              </div>
              <div className="text-center p-4 bg-[#FCE7F3]/50 rounded-xl">
                <p className="text-3xl font-bold text-[#0F172A]">{profiles.length}</p>
                <p className="text-xs text-gray-600">People Nearby</p>
              </div>
            </div>
          </div>

          {/* Nearby Preview */}
          <div className="bg-white rounded-2xl p-6 shadow-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[#0F172A]">People Nearby</h3>
              <button
                onClick={() => navigate('/dashboard/nearby')}
                className="text-sm text-[#0F172A] font-medium flex items-center gap-1 hover:underline"
              >
                View All <ChevronRight size={16} />
              </button>
            </div>
            <div className="flex -space-x-3">
              {profiles.slice(0, 4).map((profile, idx) => (
                <img
                  key={idx}
                  src={profile.profile_pictures?.[0] || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'}
                  alt={profile.name}
                  className="w-12 h-12 rounded-full border-2 border-white object-cover"
                />
              ))}
              {profiles.length > 4 && (
                <div className="w-12 h-12 rounded-full bg-[#0F172A] border-2 border-white flex items-center justify-center">
                  <span className="text-white text-xs font-semibold">+{profiles.length - 4}</span>
                </div>
              )}
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

      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center mt-8">
          <button
            onClick={loadMore}
            className="px-6 py-3 bg-[#0F172A] text-white rounded-xl hover:bg-[#1E293B] transition-colors"
          >
            Load More Profiles
          </button>
        </div>
      )}
    </div>
  );
};

export default HomePage;
