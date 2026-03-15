import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search, Flame, MapPin, Sparkles, MessageCircle,
  Coins, Eye, Heart, Users, ChevronRight, Loader2,
  TrendingUp, Star
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { userAPI } from '@/services/api';

const PLACEHOLDER_AVATAR = 'https://ui-avatars.com/api/?background=E9D5FF&color=0F172A&size=128&name=';

const SkeletonCard = () => (
  <div className="bg-white rounded-2xl p-4 shadow-sm animate-pulse">
    <div className="flex items-center gap-3">
      <div className="w-14 h-14 rounded-full bg-gray-200" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
      </div>
    </div>
  </div>
);

const SkeletonStat = () => (
  <div className="bg-white rounded-2xl p-5 shadow-sm animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-1/2 mb-2" />
    <div className="h-3 bg-gray-100 rounded w-3/4" />
  </div>
);

const HomePage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [streak, setStreak] = useState(null);
  const [streakLoading, setStreakLoading] = useState(true);

  const [nearby, setNearby] = useState([]);
  const [nearbyLoading, setNearbyLoading] = useState(true);

  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);

  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const searchRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    const fetchAll = async () => {
      await Promise.allSettled([
        fetchStreak(),
        fetchNearby(),
        fetchSuggestions(),
        fetchStats(),
      ]);
    };
    fetchAll();
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const fetchStreak = async () => {
    setStreakLoading(true);
    try {
      const res = await userAPI.getStreak();
      setStreak(res.data);
    } catch {
      setStreak({ streak_days: 1, next_reward: 5 });
    } finally {
      setStreakLoading(false);
    }
  };

  const fetchNearby = async () => {
    setNearbyLoading(true);
    try {
      const res = await userAPI.getNearby(12);
      setNearby(res.data.users || []);
    } catch {
      setNearby([]);
    } finally {
      setNearbyLoading(false);
    }
  };

  const fetchSuggestions = async () => {
    setSuggestionsLoading(true);
    try {
      const res = await userAPI.getSuggestions(3);
      setSuggestions(res.data.users || []);
    } catch {
      setSuggestions([]);
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const fetchStats = async () => {
    setStatsLoading(true);
    try {
      const res = await userAPI.getDashboardStats();
      setStats(res.data);
    } catch {
      setStats({ messages_sent: 0, matches: 0, coins: user?.coins ?? 0, profile_views: 0 });
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSearchChange = useCallback((e) => {
    const q = e.target.value;
    setSearchQuery(q);
    setShowDropdown(true);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!q.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await userAPI.search(q, 1, 8);
        setSearchResults(res.data.users || []);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);
  }, []);

  const goToProfile = (id) => {
    setShowDropdown(false);
    setSearchQuery('');
    navigate(`/dashboard/profile/${id}`);
  };

  const coinsBalance = user?.coins ?? 0;

  const statCards = [
    { icon: MessageCircle, label: 'Messages Sent', value: stats?.messages_sent ?? 0, color: 'bg-blue-50', iconColor: 'text-blue-500' },
    { icon: Heart, label: 'Matches', value: stats?.matches ?? 0, color: 'bg-rose-50', iconColor: 'text-rose-500' },
    { icon: Coins, label: 'Coins', value: coinsBalance, color: 'bg-amber-50', iconColor: 'text-amber-500' },
    { icon: Eye, label: 'Profile Views', value: stats?.profile_views ?? 0, color: 'bg-purple-50', iconColor: 'text-purple-500' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 space-y-8">

      {/* ── Welcome Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A]">
            Welcome back, {user?.name || 'there'} 👋
          </h1>
          <p className="text-gray-500 mt-1 text-sm">Find your perfect match today</p>
        </div>
        <button
          onClick={() => navigate('/dashboard/credits')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-full text-sm font-semibold text-amber-700 hover:bg-amber-100 transition-colors"
        >
          <Coins size={15} />
          {coinsBalance} coins
        </button>
      </div>

      {/* ── Search Bar ── */}
      <div className="relative" ref={searchRef}>
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search people by name…"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => searchQuery && setShowDropdown(true)}
            className="w-full pl-12 pr-12 py-3.5 bg-white border border-gray-200 rounded-2xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#0F172A]/10 focus:border-[#0F172A]/30 text-sm transition"
          />
          {isSearching && (
            <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
          )}
        </div>

        {showDropdown && searchQuery && (
          <div className="absolute z-50 top-full mt-2 w-full bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden max-h-72 overflow-y-auto">
            {searchResults.length > 0 ? (
              searchResults.map((u) => (
                <button
                  key={u.id}
                  onClick={() => goToProfile(u.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left"
                >
                  <img
                    src={u.profile_picture || `${PLACEHOLDER_AVATAR}${encodeURIComponent(u.name)}`}
                    alt={u.name}
                    className="w-10 h-10 rounded-full object-cover flex-shrink-0"
                  />
                  <div className="min-w-0">
                    <p className="font-medium text-[#0F172A] text-sm truncate">{u.name}{u.age ? `, ${u.age}` : ''}</p>
                    <p className="text-xs text-gray-400 truncate">{u.bio?.slice(0, 50) || 'No bio'}</p>
                  </div>
                  {u.is_online && (
                    <span className="ml-auto flex-shrink-0 w-2 h-2 bg-green-400 rounded-full" />
                  )}
                </button>
              ))
            ) : !isSearching ? (
              <div className="px-4 py-6 text-center text-gray-400 text-sm">
                No users found for &ldquo;{searchQuery}&rdquo;
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* ── Login Streak ── */}
      {streakLoading ? (
        <div className="h-20 bg-white rounded-2xl animate-pulse shadow-sm" />
      ) : (
        <div className="bg-gradient-to-r from-orange-50 to-amber-50 border border-amber-100 rounded-2xl p-5 flex items-center gap-4 shadow-sm">
          <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <Flame size={24} className="text-amber-500" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-[#0F172A]">
              🔥 {streak?.streak_days ?? 1} Day Streak
            </p>
            <p className="text-sm text-gray-500 mt-0.5">
              Come back tomorrow to earn {streak?.next_reward ?? 5} bonus coins
            </p>
            <div className="flex gap-1 mt-2">
              {Array.from({ length: 7 }).map((_, i) => (
                <div
                  key={i}
                  className={`h-1.5 flex-1 rounded-full ${
                    i < (streak?.streak_days ?? 1) ? 'bg-amber-400' : 'bg-amber-100'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Nearby People ── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <MapPin size={18} className="text-[#0F172A]" />
            <h2 className="font-semibold text-[#0F172A]">People Nearby</h2>
          </div>
          <button
            onClick={() => navigate('/dashboard/nearby')}
            className="text-sm text-gray-500 flex items-center gap-1 hover:text-[#0F172A] transition-colors"
          >
            View all <ChevronRight size={15} />
          </button>
        </div>

        {nearbyLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : nearby.length === 0 ? (
          <div className="bg-white rounded-2xl p-8 text-center shadow-sm">
            <Users size={36} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400 text-sm">No one nearby yet. Check back soon!</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {nearby.map((person) => (
              <button
                key={person.id}
                onClick={() => goToProfile(person.id)}
                className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all text-left group"
              >
                <div className="relative mb-3">
                  <img
                    src={person.profile_picture || `${PLACEHOLDER_AVATAR}${encodeURIComponent(person.name)}`}
                    alt={person.name}
                    className="w-14 h-14 rounded-full object-cover"
                  />
                  {person.is_online && (
                    <span className="absolute bottom-0.5 right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white" />
                  )}
                </div>
                <p className="font-medium text-[#0F172A] text-sm truncate group-hover:text-purple-700 transition-colors">
                  {person.name}{person.age ? `, ${person.age}` : ''}
                </p>
                <p className="text-xs text-gray-400 truncate mt-0.5">
                  {person.bio || person.intent || 'New member'}
                </p>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* ── Today's Match Suggestions ── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles size={18} className="text-purple-500" />
          <h2 className="font-semibold text-[#0F172A]">Today&apos;s Matches</h2>
        </div>

        {suggestionsLoading ? (
          <div className="grid sm:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="bg-white rounded-2xl overflow-hidden shadow-sm animate-pulse">
                <div className="h-48 bg-gray-200" />
                <div className="p-4 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-2/3" />
                  <div className="h-3 bg-gray-100 rounded w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : suggestions.length === 0 ? (
          <div className="bg-white rounded-2xl p-8 text-center shadow-sm">
            <Star size={36} className="text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400 text-sm">No suggestions yet. Try again later!</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-3 gap-4">
            {suggestions.map((person) => (
              <button
                key={person.id}
                onClick={() => goToProfile(person.id)}
                className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all text-left group"
              >
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={
                      person.profile_picture ||
                      `https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&auto=format&fit=crop`
                    }
                    alt={person.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  {person.is_online && (
                    <div className="absolute top-3 right-3 flex items-center gap-1 bg-green-500/90 text-white text-xs px-2 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 bg-white rounded-full" />
                      Online
                    </div>
                  )}
                  <div className="absolute bottom-3 left-3 text-white">
                    <p className="font-semibold">{person.name}{person.age ? `, ${person.age}` : ''}</p>
                  </div>
                </div>
                <div className="p-3">
                  <p className="text-xs text-gray-500 line-clamp-2">
                    {person.bio || 'Say hello and start a conversation!'}
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/dashboard/chat?user=${person.id}`); }}
                      className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-[#0F172A] text-white text-xs rounded-lg hover:bg-[#1E293B] transition-colors"
                    >
                      <MessageCircle size={12} />
                      Message
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); goToProfile(person.id); }}
                      className="flex-1 py-1.5 border border-gray-200 text-gray-600 text-xs rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      View Profile
                    </button>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {/* ── Activity Summary ── */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={18} className="text-[#0F172A]" />
          <h2 className="font-semibold text-[#0F172A]">Your Activity</h2>
        </div>

        {statsLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[0, 1, 2, 3].map((i) => <SkeletonStat key={i} />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {statCards.map(({ icon: Icon, label, value, color, iconColor }) => (
              <div key={label} className={`${color} rounded-2xl p-5 shadow-sm`}>
                <div className="flex items-center justify-between mb-3">
                  <Icon size={20} className={iconColor} />
                </div>
                <p className="text-2xl font-bold text-[#0F172A]">{value}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        )}
      </section>

    </div>
  );
};

export default HomePage;
