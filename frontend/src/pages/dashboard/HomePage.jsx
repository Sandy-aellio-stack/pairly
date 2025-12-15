import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, MessageCircle, Users, Coins, ArrowRight, Sparkles } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { locationAPI, messagesAPI } from '@/services/api';

const HomePage = () => {
  const { user, credits } = useAuthStore();
  const [nearbyCount, setNearbyCount] = useState(0);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Get user location and nearby count
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
          try {
            const response = await locationAPI.getNearby(pos.coords.latitude, pos.coords.longitude, 50);
            setNearbyCount(response.data.count || 0);
          } catch (e) {
            console.log('Failed to get nearby users');
          }
        });
      }

      // Get recent conversations
      try {
        const convResponse = await messagesAPI.getConversations();
        setConversations(convResponse.data.conversations?.slice(0, 3) || []);
      } catch (e) {
        console.log('Failed to get conversations');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Welcome Section */}
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          Welcome back, <span className="gradient-text">{user?.name?.split(' ')[0]}</span>
        </h1>
        <p className="text-white/60">Ready to make new connections today?</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        <div className="card-dark">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
              <Coins size={20} className="text-purple-400" />
            </div>
            <span className="text-white/60 text-sm">Balance</span>
          </div>
          <div className="text-3xl font-bold gradient-text">{credits}</div>
          <p className="text-white/40 text-sm">coins available</p>
        </div>

        <div className="card-dark">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
              <Users size={20} className="text-green-400" />
            </div>
            <span className="text-white/60 text-sm">Nearby</span>
          </div>
          <div className="text-3xl font-bold text-green-400">{nearbyCount}</div>
          <p className="text-white/40 text-sm">people near you</p>
        </div>

        <div className="card-dark">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <MessageCircle size={20} className="text-blue-400" />
            </div>
            <span className="text-white/60 text-sm">Chats</span>
          </div>
          <div className="text-3xl font-bold text-blue-400">{conversations.length}</div>
          <p className="text-white/40 text-sm">conversations</p>
        </div>

        <Link to="/dashboard/credits" className="card-dark group hover:border-purple-500/30 transition-colors">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center">
              <Sparkles size={20} className="text-pink-400" />
            </div>
            <span className="text-white/60 text-sm">Buy More</span>
          </div>
          <div className="text-lg font-bold text-pink-400">Get Coins</div>
          <ArrowRight size={16} className="text-white/40 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-10">
        <Link
          to="/dashboard/nearby"
          className="card-dark flex items-center gap-6 group hover:border-purple-500/30 transition-all"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center group-hover:scale-110 transition-transform">
            <MapPin size={32} className="text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold mb-1">Discover Nearby</h3>
            <p className="text-white/60">Find people around you on the map</p>
          </div>
          <ArrowRight size={24} className="text-white/40 group-hover:text-purple-400 group-hover:translate-x-2 transition-all" />
        </Link>

        <Link
          to="/dashboard/chat"
          className="card-dark flex items-center gap-6 group hover:border-purple-500/30 transition-all"
        >
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center group-hover:scale-110 transition-transform">
            <MessageCircle size={32} className="text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold mb-1">Messages</h3>
            <p className="text-white/60">Continue your conversations</p>
          </div>
          <ArrowRight size={24} className="text-white/40 group-hover:text-purple-400 group-hover:translate-x-2 transition-all" />
        </Link>
      </div>

      {/* Recent Conversations */}
      {conversations.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">Recent Conversations</h2>
            <Link to="/dashboard/chat" className="text-purple-400 text-sm hover:underline">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {conversations.map((conv) => (
              <Link
                key={conv.conversation_id}
                to={`/dashboard/chat/${conv.user.id}`}
                className="card-dark flex items-center gap-4 py-4 hover:border-purple-500/30 transition-colors"
              >
                <div className="relative">
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center overflow-hidden">
                    {conv.user.profile_picture ? (
                      <img src={conv.user.profile_picture} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-lg font-bold text-purple-400">{conv.user.name?.[0]}</span>
                    )}
                  </div>
                  {conv.user.is_online && (
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-[#0B0B0F]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold truncate">{conv.user.name}</h4>
                    {conv.unread_count > 0 && (
                      <span className="bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-white/40 text-sm truncate">{conv.last_message}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
