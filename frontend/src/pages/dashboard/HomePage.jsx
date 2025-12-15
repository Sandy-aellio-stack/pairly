import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MessageCircle, MapPin, Sparkles } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { locationAPI, messagesAPI } from '@/services/api';
import gsap from 'gsap';

const HomePage = () => {
  const { user, credits } = useAuthStore();
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Animate cards on load
    gsap.from('.user-card', {
      y: 40,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: 'power3.out',
    });
  }, [nearbyUsers]);

  const loadData = async () => {
    try {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
          try {
            const response = await locationAPI.getNearby(pos.coords.latitude, pos.coords.longitude, 50);
            setNearbyUsers(response.data.users || []);
            // Create stories from nearby users
            setStories(response.data.users?.slice(0, 8) || []);
          } catch (e) {
            // Mock data for demo
            const mockUsers = [
              { id: '1', name: 'Sarah', age: 24, distance_km: 2.5, bio: 'Coffee lover ☕', is_online: true },
              { id: '2', name: 'Emma', age: 26, distance_km: 3.1, bio: 'Travel enthusiast ✈️', is_online: true },
              { id: '3', name: 'Mia', age: 23, distance_km: 4.2, bio: 'Yoga & meditation 🧘', is_online: false },
              { id: '4', name: 'Ava', age: 25, distance_km: 5.0, bio: 'Art & music 🎨', is_online: true },
            ];
            setNearbyUsers(mockUsers);
            setStories(mockUsers);
          }
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Hey, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-gray-500">Ready to find your bond today?</p>
      </div>

      {/* Stories */}
      <div className="mb-8">
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
          {/* Your Story */}
          <div className="flex-shrink-0 text-center">
            <div className="w-[72px] h-[72px] rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-dashed border-purple-300 flex items-center justify-center mb-2">
              <span className="text-2xl">+</span>
            </div>
            <span className="text-xs text-gray-600">Your Story</span>
          </div>
          
          {/* Other Stories */}
          {stories.map((story, i) => (
            <div key={story.id || i} className="flex-shrink-0 text-center story-bubble-wrapper">
              <div className="story-bubble">
                <div className="story-bubble-inner bg-gradient-to-br from-purple-300 to-pink-300 flex items-center justify-center">
                  <span className="text-white text-xl font-bold">{story.name?.[0]}</span>
                </div>
              </div>
              <span className="text-xs text-gray-600 mt-2 block truncate w-16">{story.name?.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Feed */}
      <div className="space-y-6">
        {loading ? (
          <div className="text-center py-20">
            <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-500">Finding people nearby...</p>
          </div>
        ) : nearbyUsers.length === 0 ? (
          <div className="text-center py-20 card">
            <Sparkles size={48} className="text-purple-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold mb-2">No one nearby yet</h3>
            <p className="text-gray-500 mb-4">Enable location to discover people around you</p>
            <Link to="/dashboard/nearby" className="btn-primary inline-block">
              Enable Location
            </Link>
          </div>
        ) : (
          nearbyUsers.map((person) => (
            <div key={person.id} className="user-card">
              {/* Header */}
              <div className="flex items-center gap-3 p-4 border-b border-gray-100">
                <div className="relative">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-lg">
                    {person.name?.[0]}
                  </div>
                  {person.is_online && (
                    <div className="absolute bottom-0 right-0 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{person.name}, {person.age}</h3>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    <MapPin size={12} /> {person.distance_km}km away
                  </p>
                </div>
              </div>

              {/* Image placeholder */}
              <div className="aspect-square bg-gradient-to-br from-purple-100 via-pink-50 to-purple-50 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white text-4xl font-bold mx-auto mb-4">
                    {person.name?.[0]}
                  </div>
                  {person.bio && (
                    <p className="text-gray-600 px-4">{person.bio}</p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-4 p-4">
                <button className="flex items-center gap-2 text-gray-600 hover:text-red-500 transition-colors">
                  <Heart size={24} />
                </button>
                <Link
                  to={`/dashboard/chat/${person.id}`}
                  className="flex items-center gap-2 text-gray-600 hover:text-purple-500 transition-colors"
                >
                  <MessageCircle size={24} />
                </Link>
                <div className="ml-auto text-sm text-gray-400">
                  1 coin to message
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default HomePage;
