import { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Filter, MapPin, Heart, X, MessageCircle, Users, Loader2, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { locationAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const ageRanges = ['18-25', '20-30', '25-35', '30-40', '35-45', '40+'];
const genders = ['All', 'Male', 'Female', 'Other'];
const interestOptions = ['Hiking', 'Coffee', 'Music', 'Travel', 'Photography', 'Art', 'Gaming', 'Tech', 'Yoga', 'Reading', 'Fitness', 'Cooking'];

const NearbyPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});
  
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [ageRange, setAgeRange] = useState('20-30');
  const [gender, setGender] = useState('All');
  const [interests, setInterests] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userLocation, setUserLocation] = useState({ lat: 12.9716, lng: 77.5946 }); // Default: Bangalore
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch nearby users
  const fetchNearbyUsers = async (lat, lng) => {
    setIsLoading(true);
    try {
      // First update our location
      await locationAPI.update(lat, lng);
      
      // Then fetch nearby users
      const response = await locationAPI.getNearby(lat, lng, user?.preferences?.max_distance_km || 50);
      
      if (response.data.users && response.data.users.length > 0) {
        // Filter to only include users with valid location data
        const usersWithLocations = response.data.users
          .filter(u => u.location && u.location.lat && u.location.lng)
          .map((u) => ({
            ...u,
            photo: u.profile_pictures?.[0] || '',
            lookingFor: u.intent || 'dating',
            interests: u.interests || []
          }));
        setUsers(usersWithLocations);
      } else {
        setUsers([]);
      }
    } catch (error) {
      console.error('Error fetching nearby users:', error);
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Get user location and fetch nearby users
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          fetchNearbyUsers(latitude, longitude);
        },
        () => {
          // Geolocation denied, use default
          fetchNearbyUsers(userLocation.lat, userLocation.lng);
        }
      );
    } else {
      fetchNearbyUsers(userLocation.lat, userLocation.lng);
    }
  }, []);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    // Using OpenStreetMap tiles via MapLibre (free, no API key needed)
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap Contributors',
          },
        },
        layers: [
          {
            id: 'osm',
            type: 'raster',
            source: 'osm',
          },
        ],
      },
      center: [userLocation.lng, userLocation.lat],
      zoom: 13,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Add markers when map loads
    map.current.on('load', () => {
      addMarkers();
    });

    return () => {
      Object.values(markersRef.current).forEach(marker => marker.remove());
      map.current?.remove();
    };
  }, []);

  // Update map center when user location changes
  useEffect(() => {
    if (map.current && userLocation) {
      map.current.flyTo({
        center: [userLocation.lng, userLocation.lat],
        zoom: 13,
        duration: 1000
      });
    }
  }, [userLocation]);

  // Add markers for users
  const addMarkers = () => {
    if (!map.current) return;

    // Remove existing markers
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    users.forEach((user) => {
      if (!user.location) return;

      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'user-marker';
      el.innerHTML = `
        <div class="relative cursor-pointer transition-transform hover:scale-110 ${selectedUser?.id === user.id ? 'scale-125' : ''}">
          <div class="w-12 h-12 rounded-full border-3 border-white shadow-lg overflow-hidden ${selectedUser?.id === user.id ? 'ring-4 ring-rose-400' : ''}" style="border: 3px solid white;">
            <img src="${user.photo}" alt="${user.name}" style="width: 100%; height: 100%; object-fit: cover;" />
          </div>
          <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white" style="border: 2px solid white;"></div>
        </div>
      `;

      el.addEventListener('click', () => {
        setSelectedUser(user);
        map.current?.flyTo({
          center: [user.location.lng, user.location.lat],
          zoom: 15,
          duration: 500
        });
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([user.location.lng, user.location.lat])
        .addTo(map.current);

      markersRef.current[user.id] = marker;
    });
  };

  // Update markers when selected user or users list changes
  useEffect(() => {
    if (map.current?.isStyleLoaded()) {
      addMarkers();
    }
  }, [selectedUser, users]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchNearbyUsers(userLocation.lat, userLocation.lng);
    setIsRefreshing(false);
    toast.success('Refreshed nearby users');
  };

  const handleConnect = (user) => {
    if ((useAuthStore.getState().user?.credits_balance || 0) > 0) {
      navigate('/dashboard/chat');
    } else {
      toast.error('You need coins to send messages!');
      navigate('/dashboard/credits');
    }
  };

  const toggleInterest = (interest) => {
    if (interests.includes(interest)) {
      setInterests(interests.filter(i => i !== interest));
    } else {
      setInterests([...interests, interest]);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setAgeRange('20-30');
    setGender('All');
    setInterests([]);
  };

  // Filter users based on search and filters
  const filteredUsers = users.filter(user => {
    if (searchQuery && !user.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    // Add more filter logic as needed
    return true;
  });

  return (
    <div className="h-[calc(100vh-140px)] bg-[#F8FAFC] flex flex-col lg:flex-row">
      {/* Left Panel - User List */}
      <div className="w-full lg:w-[420px] flex flex-col border-b lg:border-b-0 lg:border-r border-gray-200 bg-white h-1/2 lg:h-full">
        {/* Header */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-[#0F172A]">Nearby People</h1>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <RefreshCw size={20} className={`text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
          
          {/* Search Bar */}
          <div className="relative mb-4">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search nearby..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none text-sm"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-[#0F172A]"
          >
            <Filter size={16} />
            Filters
            <ChevronDown size={16} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 p-4 bg-gray-50 rounded-xl space-y-4">
              <div>
                <label className="text-xs font-medium text-gray-500 mb-2 block">Age Range</label>
                <div className="flex flex-wrap gap-2">
                  {ageRanges.map(range => (
                    <button
                      key={range}
                      onClick={() => setAgeRange(range)}
                      className={`px-3 py-1 text-xs rounded-full transition-all ${
                        ageRange === range
                          ? 'bg-[#0F172A] text-white'
                          : 'bg-white border border-gray-200 text-gray-600 hover:border-[#0F172A]'
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500 mb-2 block">Gender</label>
                <div className="flex flex-wrap gap-2">
                  {genders.map(g => (
                    <button
                      key={g}
                      onClick={() => setGender(g)}
                      className={`px-3 py-1 text-xs rounded-full transition-all ${
                        gender === g
                          ? 'bg-[#0F172A] text-white'
                          : 'bg-white border border-gray-200 text-gray-600 hover:border-[#0F172A]'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500 mb-2 block">Interests</label>
                <div className="flex flex-wrap gap-2">
                  {interestOptions.slice(0, 8).map(interest => (
                    <button
                      key={interest}
                      onClick={() => toggleInterest(interest)}
                      className={`px-3 py-1 text-xs rounded-full transition-all ${
                        interests.includes(interest)
                          ? 'bg-[#E9D5FF] text-[#0F172A]'
                          : 'bg-white border border-gray-200 text-gray-600 hover:border-[#E9D5FF]'
                      }`}
                    >
                      {interest}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={clearFilters}
                className="text-xs text-gray-500 hover:text-[#0F172A]"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>

        {/* User List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-[#0F172A] mx-auto mb-2" />
                <p className="text-gray-500 text-sm">Finding people nearby...</p>
              </div>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Users size={32} className="text-gray-300 mb-2" />
              <p className="text-gray-500 text-sm">No one nearby yet</p>
              <p className="text-gray-400 text-xs">Check back later!</p>
            </div>
          ) : (
            filteredUsers.map((user) => (
              <div
                key={user.id}
                onClick={() => {
                  setSelectedUser(user);
                  if (map.current && user.location) {
                    map.current.flyTo({
                      center: [user.location.lng, user.location.lat],
                      zoom: 15,
                      duration: 500
                    });
                  }
                }}
                className={`flex gap-4 p-4 bg-white rounded-xl shadow-sm cursor-pointer transition-all hover:shadow-md ${
                  selectedUser?.id === user.id ? 'ring-2 ring-[#0F172A] shadow-md' : 'border border-gray-100'
                }`}
              >
                <img
                  src={user.photo || user.profile_pictures?.[0]}
                  alt={user.name}
                  className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-[#0F172A]">
                      {user.name}, {user.age}
                    </h3>
                    <button className="text-gray-400 hover:text-rose-500 transition-colors">
                      <Heart size={18} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                    <MapPin size={12} />
                    {user.distance_km?.toFixed(1) || '?'} km away
                  </p>
                  <p className="text-xs text-gray-600 mt-2 truncate">
                    {user.interests?.join(' • ') || 'No interests listed'}
                  </p>
                  <p className="text-xs text-[#0F172A] font-medium mt-1">
                    {user.lookingFor || user.intent || 'Looking to connect'}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative min-h-[300px] lg:min-h-0">
        <div ref={mapContainer} className="absolute inset-0" />
        
        {/* Selected User Popup */}
        {selectedUser && (
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 bg-white rounded-2xl shadow-2xl p-6 w-80 z-10">
            <button
              onClick={() => setSelectedUser(null)}
              className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
            >
              <X size={20} />
            </button>
            
            <div className="flex items-center gap-4 mb-4">
              <img
                src={selectedUser.photo || selectedUser.profile_pictures?.[0]}
                alt={selectedUser.name}
                className="w-16 h-16 rounded-full object-cover border-2 border-[#E9D5FF]"
              />
              <div>
                <h3 className="text-lg font-bold text-[#0F172A]">
                  {selectedUser.name}, {selectedUser.age}
                </h3>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <MapPin size={14} />
                  {selectedUser.distance_km?.toFixed(1) || '?'} km away
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {(selectedUser.interests || []).map((interest, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-[#E9D5FF]/50 text-[#0F172A] rounded-full text-xs"
                >
                  {interest}
                </span>
              ))}
            </div>
            
            <p className="text-sm text-gray-600 mb-4">
              <span className="font-medium">Looking for:</span> {selectedUser.lookingFor || selectedUser.intent || 'Connection'}
            </p>
            
            <div className="flex gap-3">
              <button 
                onClick={() => handleConnect(selectedUser)}
                className="flex-1 py-3 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2"
              >
                <MessageCircle size={18} />
                Connect
              </button>
              <button className="p-3 border border-gray-200 rounded-xl hover:bg-gray-50 transition-all">
                <Heart size={18} className="text-rose-500" />
              </button>
            </div>
          </div>
        )}

        {/* Map Stats */}
        <div className="absolute top-4 left-4 bg-white rounded-xl shadow-lg px-4 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Users size={18} className="text-[#0F172A]" />
            <span className="text-sm font-medium text-[#0F172A]">{filteredUsers.length} nearby</span>
          </div>
        </div>

        {/* Map Notice */}
        <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 text-xs text-gray-500">
          © OpenStreetMap contributors
        </div>
      </div>
    </div>
  );
};

export default NearbyPage;
