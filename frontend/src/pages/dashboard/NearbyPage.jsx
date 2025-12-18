import { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, Filter, MapPin, Heart, X, MessageCircle, Users } from 'lucide-react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// Mock users data
const mockUsers = [
  {
    id: '1',
    name: 'Priya',
    age: 26,
    photo: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200',
    interests: ['Hiking', 'Photography', 'Coffee'],
    lookingFor: 'Long-term relationship',
    distance: '2.5 km away',
    location: { lat: 12.9716, lng: 77.5946 }
  },
  {
    id: '2',
    name: 'Arjun',
    age: 28,
    photo: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200',
    interests: ['Music', 'Travel', 'Tech'],
    lookingFor: 'Meaningful connection',
    distance: '3.2 km away',
    location: { lat: 12.9756, lng: 77.5996 }
  },
  {
    id: '3',
    name: 'Ananya',
    age: 24,
    photo: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200',
    interests: ['Art', 'Yoga', 'Reading'],
    lookingFor: 'Friendship first',
    distance: '4.1 km away',
    location: { lat: 12.9686, lng: 77.5906 }
  },
  {
    id: '4',
    name: 'Rahul',
    age: 30,
    photo: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200',
    interests: ['Fitness', 'Cooking', 'Movies'],
    lookingFor: 'Serious relationship',
    distance: '5.0 km away',
    location: { lat: 12.9796, lng: 77.6006 }
  },
  {
    id: '5',
    name: 'Sneha',
    age: 27,
    photo: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200',
    interests: ['Dancing', 'Travel', 'Food'],
    lookingFor: 'Someone genuine',
    distance: '6.3 km away',
    location: { lat: 12.9666, lng: 77.6046 }
  }
];

const ageRanges = ['18-25', '20-30', '25-35', '30-40', '35-45', '40+'];
const genders = ['All', 'Male', 'Female', 'Non-binary'];
const interestOptions = ['Hiking', 'Coffee', 'Music', 'Travel', 'Photography', 'Art', 'Gaming', 'Tech', 'Yoga', 'Reading', 'Fitness', 'Cooking'];

const NearbyPage = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef({});
  
  const [users, setUsers] = useState(mockUsers);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [ageRange, setAgeRange] = useState('20-30');
  const [gender, setGender] = useState('All');
  const [interests, setInterests] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [77.5946, 12.9716], // Bangalore
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

  // Add markers for users
  const addMarkers = () => {
    if (!map.current) return;

    // Remove existing markers
    Object.values(markersRef.current).forEach(marker => marker.remove());
    markersRef.current = {};

    users.forEach((user) => {
      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'user-marker';
      el.innerHTML = `
        <div class="relative cursor-pointer transition-transform hover:scale-110 ${selectedUser?.id === user.id ? 'scale-125' : ''}">
          <div class="w-12 h-12 rounded-full border-3 border-white shadow-lg overflow-hidden ${selectedUser?.id === user.id ? 'ring-4 ring-rose-400' : ''}">
            <img src="${user.photo}" alt="${user.name}" class="w-full h-full object-cover" />
          </div>
          <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></div>
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

  // Update markers when selected user changes
  useEffect(() => {
    if (map.current?.isStyleLoaded()) {
      addMarkers();
    }
  }, [selectedUser, users]);

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

  return (
    <div className="h-screen bg-[#F8FAFC] flex">
      {/* Left Panel - User List */}
      <div className="w-full lg:w-[420px] flex flex-col border-r border-gray-200 bg-white">
        {/* Header */}
        <div className="p-4 border-b border-gray-100">
          <h1 className="text-2xl font-bold text-[#0F172A] mb-4">Nearby People</h1>
          
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
          {users.map((user) => (
            <div
              key={user.id}
              onClick={() => {
                setSelectedUser(user);
                map.current?.flyTo({
                  center: [user.location.lng, user.location.lat],
                  zoom: 15,
                  duration: 500
                });
              }}
              className={`flex gap-4 p-4 bg-white rounded-xl shadow-sm cursor-pointer transition-all hover:shadow-md ${
                selectedUser?.id === user.id ? 'ring-2 ring-[#0F172A] shadow-md' : 'border border-gray-100'
              }`}
            >
              <img
                src={user.photo}
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
                  {user.distance}
                </p>
                <p className="text-xs text-gray-600 mt-2 truncate">
                  {user.interests.join(' • ')}
                </p>
                <p className="text-xs text-[#0F172A] font-medium mt-1">
                  {user.lookingFor}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Map */}
      <div className="hidden lg:block flex-1 relative">
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
                src={selectedUser.photo}
                alt={selectedUser.name}
                className="w-16 h-16 rounded-full object-cover border-2 border-[#E9D5FF]"
              />
              <div>
                <h3 className="text-lg font-bold text-[#0F172A]">
                  {selectedUser.name}, {selectedUser.age}
                </h3>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <MapPin size={14} />
                  {selectedUser.distance}
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedUser.interests.map((interest, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 bg-[#E9D5FF]/50 text-[#0F172A] rounded-full text-xs"
                >
                  {interest}
                </span>
              ))}
            </div>
            
            <p className="text-sm text-gray-600 mb-4">
              <span className="font-medium">Looking for:</span> {selectedUser.lookingFor}
            </p>
            
            <div className="flex gap-3">
              <button className="flex-1 py-3 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all flex items-center justify-center gap-2">
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
            <span className="text-sm font-medium text-[#0F172A]">{users.length} nearby</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NearbyPage;
