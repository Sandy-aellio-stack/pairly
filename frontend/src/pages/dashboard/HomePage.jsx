import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Heart, MessageCircle, MapPin, Sparkles, Plus, X } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { locationAPI } from '@/services/api';
import gsap from 'gsap';

const HomePage = () => {
  const { user, credits } = useAuthStore();
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [likedUsers, setLikedUsers] = useState(new Set());

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (nearbyUsers.length > 0) {
      gsap.from('.user-card', {
        y: 40,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: 'power3.out',
      });
    }
  }, [nearbyUsers]);

  const loadData = async () => {
    try {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
          try {
            const response = await locationAPI.getNearby(pos.coords.latitude, pos.coords.longitude, 50);
            setNearbyUsers(response.data.users || []);
            setStories(response.data.users?.slice(0, 8) || []);
          } catch (e) {
            // Mock data for demo
            const mockUsers = [
              { id: '1', name: 'Sarah', age: 24, distance_km: 2.5, bio: 'Coffee lover ☕ | Travel enthusiast', is_online: true },
              { id: '2', name: 'Emma', age: 26, distance_km: 3.1, bio: 'Yoga & meditation 🧘‍♀️', is_online: true },
              { id: '3', name: 'Mia', age: 23, distance_km: 4.2, bio: 'Art & music lover 🎨🎵', is_online: false },
              { id: '4', name: 'Ava', age: 25, distance_km: 5.0, bio: 'Adventure seeker 🌍', is_online: true },
              { id: '5', name: 'Olivia', age: 27, distance_km: 6.3, bio: 'Foodie | Dog mom 🐕', is_online: false },
            ];
            setNearbyUsers(mockUsers);
            setStories(mockUsers);
          }
        });
      } else {
        // Mock data if geolocation not available
        const mockUsers = [
          { id: '1', name: 'Sarah', age: 24, distance_km: 2.5, bio: 'Coffee lover ☕', is_online: true },
          { id: '2', name: 'Emma', age: 26, distance_km: 3.1, bio: 'Travel enthusiast ✈️', is_online: true },
        ];
        setNearbyUsers(mockUsers);
        setStories(mockUsers);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLike = (userId) => {
    setLikedUsers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(userId)) {
        newSet.delete(userId);
      } else {
        newSet.add(userId);
      }
      return newSet;
    });
  };

  const gradients = [
    'from-purple-400 to-pink-400',
    'from-blue-400 to-cyan-400',
    'from-orange-400 to-red-400',
    'from-green-400 to-teal-400',
    'from-indigo-400 to-purple-400',
  ];

  return (
    <div className="max-w-2xl mx-auto">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          Hey, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-gray-500">Ready to find your bond today?</p>
      </div>

      {/* Stories Section */}
      <div className="mb-8">
        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide -mx-4 px-4">
          {/* Your Story */}
          <div className="flex-shrink-0 text-center">
            <div className="relative">
              <div className="w-[72px] h-[72px] rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-dashed border-purple-300 flex items-center justify-center mb-2">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-lg">
                  {user?.name?.[0]}
                </div>
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-purple-500 border-2 border-white flex items-center justify-center">
                <Plus size={14} className="text-white" />
              </div>
            </div>
            <span className="text-xs text-gray-600 mt-2 block">Your Story</span>
          </div>
          
          {/* Other Stories */}
          {stories.map((story, i) => (
            <div key={story.id || i} className="flex-shrink-0 text-center story-bubble-wrapper">
              <div className="story-bubble">
                <div className={`story-bubble-inner bg-gradient-to-br ${gradients[i % gradients.length]} flex items-center justify-center`}>
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
            <h3 className="text-lg font-bold text-gray-900 mb-2">No one nearby yet</h3>
            <p className="text-gray-500 mb-4">Enable location to discover people around you</p>
            <Link to="/dashboard/nearby" className="btn-primary inline-block">
              Enable Location
            </Link>
          </div>
        ) : (
          nearbyUsers.map((person, index) => (
            <div key={person.id} className="user-card">
              {/* Header */}
              <div className="flex items-center gap-3 p-4 border-b border-gray-100">
                <div className="relative">
                  <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${gradients[index % gradients.length]} flex items-center justify-center text-white font-bold text-lg`}>
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

              {/* Image/Profile Display */}
              <div className="aspect-[4/5] bg-gradient-to-br from-purple-50 via-pink-50 to-purple-100 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 opacity-30">
                  <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-purple-300 blur-3xl" />
                  <div className="absolute bottom-20 right-10 w-40 h-40 rounded-full bg-pink-300 blur-3xl" />
                </div>
                <div className="text-center relative z-10">
                  <div className={`w-32 h-32 rounded-full bg-gradient-to-br ${gradients[index % gradients.length]} flex items-center justify-center text-white text-5xl font-bold mx-auto mb-6 shadow-xl`}>
                    {person.name?.[0]}
                  </div>
                  {person.bio && (
                    <p className="text-gray-700 px-6 text-lg">{person.bio}</p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-4 p-4">
                <button 
                  onClick={() => handleLike(person.id)}
                  className={`flex items-center gap-2 transition-colors ${
                    likedUsers.has(person.id) ? 'text-red-500' : 'text-gray-600 hover:text-red-500'
                  }`}
                >
                  <Heart size={26} fill={likedUsers.has(person.id) ? 'currentColor' : 'none'} />
                </button>
                <Link
                  to={`/dashboard/chat/${person.id}`}
                  className="flex items-center gap-2 text-gray-600 hover:text-purple-500 transition-colors"
                >
                  <MessageCircle size={26} />
                </Link>
                <div className="ml-auto flex items-center gap-2 text-sm text-gray-400">
                  <span className="bg-purple-100 text-purple-600 px-2 py-1 rounded-full text-xs font-medium">1 coin to message</span>
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
