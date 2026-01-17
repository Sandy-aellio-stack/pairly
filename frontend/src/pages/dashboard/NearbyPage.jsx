import { useState, useEffect, useRef } from 'react';
import { Search, Filter, MapPin, Heart, X, MessageCircle, Users, Loader2, RefreshCw, List, Map as MapIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { locationAPI, userAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

// Mapbox access token
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoibHV2ZWxvb3AiLCJhIjoiY21raWZkZjFhMHFkbjNoc2NtdmE2cmxiNSJ9.9pV12IAA86TH5jZI8UOsdw';

const NearbyPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const mapContainer = useRef(null);
  const map = useRef(null);
  const markersRef = useRef([]);
  
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [userLocation, setUserLocation] = useState({ lat: 12.9716, lng: 77.5946 });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'list'

  // Fetch users
  const fetchUsers = async (lat, lng) => {
    setIsLoading(true);
    try {
      // Try to update location
      try {
        await locationAPI.update(lat, lng);
      } catch (e) {
        console.log('Could not update location');
      }
      
      // Get users from feed (more reliable than nearby)
      let usersData = [];
      try {
        const feedResponse = await userAPI.getFeed(1, 50);
        if (feedResponse.data.users && feedResponse.data.users.length > 0) {
          usersData = feedResponse.data.users;
        }
      } catch (e) {
        console.log('Feed API failed:', e);
      }
      
      // Format users with location for map
      const formattedUsers = usersData.map((u, index) => ({
        ...u,
        photo: u.profile_pictures?.[0] || `https://api.dicebear.com/7.x/avataaars/svg?seed=${u.name || index}`,
        location: u.location || {
          lat: lat + (Math.random() - 0.5) * 0.08,
          lng: lng + (Math.random() - 0.5) * 0.08
        }
      }));
      
      setUsers(formattedUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Get location and fetch users
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          fetchUsers(latitude, longitude);
        },
        () => {
          fetchUsers(userLocation.lat, userLocation.lng);
        }
      );
    } else {
      fetchUsers(userLocation.lat, userLocation.lng);
    }
  }, []);

  // Initialize Mapbox using callback ref
  const initializeMap = (container) => {
    if (!container || map.current) return;
    
    console.log('Initializing map with container:', container);
    
    try {
      map.current = new mapboxgl.Map({
        container: container,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: [userLocation.lng, userLocation.lat],
        zoom: 11,
        attributionControl: false
      });

      map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

      map.current.on('load', () => {
        console.log('Map loaded successfully');
        addMarkers();
      });
      
      map.current.on('error', (e) => {
        console.error('Mapbox error:', e);
      });
    } catch (err) {
      console.error('Failed to initialize map:', err);
    }
  };
  
  // Cleanup map on unmount
  useEffect(() => {
    return () => {
      if (map.current) {
        markersRef.current.forEach(marker => marker.remove());
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update map when location changes
  useEffect(() => {
    if (map.current && userLocation) {
      map.current.flyTo({
        center: [userLocation.lng, userLocation.lat],
        zoom: 11,
        duration: 1000
      });
    }
  }, [userLocation]);

  // Add user markers
  const addMarkers = () => {
    if (!map.current) return;

    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    users.forEach((userItem) => {
      const lat = userItem.location?.lat || userItem.location?.latitude;
      const lng = userItem.location?.lng || userItem.location?.longitude;
      
      if (!lat || !lng) return;

      const el = document.createElement('div');
      el.innerHTML = `
        <div style="cursor: pointer; transition: transform 0.2s;">
          <div style="width: 50px; height: 50px; border-radius: 50%; border: 3px solid white; box-shadow: 0 4px 12px rgba(0,0,0,0.3); overflow: hidden; background: white;">
            <img src="${userItem.photo}" alt="${userItem.name}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='https://api.dicebear.com/7.x/avataaars/svg?seed=${userItem.name}'" />
          </div>
          <div style="position: absolute; bottom: -2px; right: -2px; width: 14px; height: 14px; background: #22c55e; border-radius: 50%; border: 2px solid white;"></div>
        </div>
      `;

      el.addEventListener('click', () => {
        setSelectedUser(userItem);
        map.current?.flyTo({ center: [lng, lat], zoom: 14, duration: 500 });
      });

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([lng, lat])
        .addTo(map.current);

      markersRef.current.push(marker);
    });
  };

  useEffect(() => {
    if (map.current?.isStyleLoaded()) {
      addMarkers();
    }
  }, [users]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchUsers(userLocation.lat, userLocation.lng);
    setIsRefreshing(false);
    toast.success('Refreshed!');
  };

  const handleMessage = (userItem) => {
    if ((user?.credits_balance || 0) > 0) {
      navigate(`/dashboard/chat?user=${userItem.id}`);
    } else {
      toast.error('You need coins to send messages!');
      navigate('/dashboard/credits');
    }
  };

  const handleViewProfile = (userId) => {
    navigate(`/dashboard/profile/${userId}`);
  };

  const filteredUsers = users.filter(u => {
    if (searchQuery && !u.name?.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <div className="h-full flex flex-col" style={{ minHeight: 'calc(100vh - 200px)' }}>
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-xl font-bold text-[#0F172A]">Nearby People</h1>
          
          {/* Search */}
          <div className="flex-1 max-w-md relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 focus:border-[#0F172A] focus:ring-1 focus:ring-[#0F172A] outline-none text-sm"
            />
          </div>
          
          {/* View toggle & Refresh */}
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('map')}
                className={`p-2 rounded-md transition-colors ${viewMode === 'map' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              >
                <MapIcon size={18} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition-colors ${viewMode === 'list' ? 'bg-white shadow-sm' : 'text-gray-500'}`}
              >
                <List size={18} />
              </button>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw size={18} className={`text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 relative" id="nearby-map-container" style={{ minHeight: '500px' }}>
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <Loader2 className="w-10 h-10 animate-spin text-[#0F172A] mx-auto mb-3" />
              <p className="text-gray-500">Finding people nearby...</p>
            </div>
          </div>
        ) : viewMode === 'map' ? (
          <div className="relative w-full h-full" style={{ minHeight: '500px' }}>
            {/* Full-width Map */}
            <div ref={initializeMap} className="absolute inset-0" />
            
            {/* User count badge */}
            <div className="absolute top-4 left-4 bg-white rounded-full px-4 py-2 shadow-lg flex items-center gap-2 z-10">
              <Users size={18} className="text-[#0F172A]" />
              <span className="font-semibold">{filteredUsers.length} nearby</span>
            </div>

            {/* User list overlay (left side) */}
            <div className="absolute left-4 top-16 bottom-4 w-80 bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden z-10">
              <div className="p-3 border-b bg-white">
                <p className="text-sm font-medium text-gray-600">{filteredUsers.length} people found</p>
              </div>
              <div className="overflow-y-auto h-[calc(100%-50px)] p-3 space-y-3">
                {filteredUsers.map((userItem) => (
                  <div
                    key={userItem.id}
                    onClick={() => {
                      setSelectedUser(userItem);
                      const lat = userItem.location?.lat;
                      const lng = userItem.location?.lng;
                      if (map.current && lat && lng) {
                        map.current.flyTo({ center: [lng, lat], zoom: 14, duration: 500 });
                      }
                    }}
                    className={`flex gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                      selectedUser?.id === userItem.id ? 'bg-[#0F172A] text-white' : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <img
                      src={userItem.photo}
                      alt={userItem.name}
                      className="w-14 h-14 object-cover rounded-lg flex-shrink-0"
                      onError={(e) => { e.target.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userItem.name}`; }}
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold truncate">{userItem.name}, {userItem.age}</h3>
                      <p className={`text-xs mt-0.5 flex items-center gap-1 ${selectedUser?.id === userItem.id ? 'text-gray-300' : 'text-gray-500'}`}>
                        <MapPin size={12} />
                        {userItem.distance_display || 'Nearby'}
                      </p>
                      <p className={`text-xs mt-1 capitalize ${selectedUser?.id === userItem.id ? 'text-gray-300' : 'text-gray-600'}`}>
                        {userItem.intent || 'Dating'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected user popup */}
            {selectedUser && (
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white rounded-2xl shadow-2xl p-5 w-96 z-20">
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
                    className="w-16 h-16 rounded-full object-cover border-2 border-gray-100"
                    onError={(e) => { e.target.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${selectedUser.name}`; }}
                  />
                  <div>
                    <h3 className="text-lg font-bold text-[#0F172A]">{selectedUser.name}, {selectedUser.age}</h3>
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      <MapPin size={14} />
                      {selectedUser.distance_display || 'Nearby'}
                    </p>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">{selectedUser.bio || 'No bio yet'}</p>
                
                <div className="flex gap-3">
                  <button 
                    onClick={() => handleViewProfile(selectedUser.id)}
                    className="flex-1 py-2.5 bg-gray-100 text-[#0F172A] rounded-xl font-medium hover:bg-gray-200 transition-colors"
                  >
                    View Profile
                  </button>
                  <button 
                    onClick={() => handleMessage(selectedUser)}
                    className="flex-1 py-2.5 bg-[#0F172A] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                  >
                    <MessageCircle size={18} />
                    Message
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* List View */
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 overflow-y-auto h-full">
            {filteredUsers.map((userItem) => (
              <div
                key={userItem.id}
                className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="aspect-square relative">
                  <img
                    src={userItem.photo}
                    alt={userItem.name}
                    className="w-full h-full object-cover"
                    onError={(e) => { e.target.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${userItem.name}`; }}
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                    <h3 className="text-white font-bold text-lg">{userItem.name}, {userItem.age}</h3>
                    <p className="text-white/80 text-sm flex items-center gap-1">
                      <MapPin size={12} />
                      {userItem.distance_display || 'Nearby'}
                    </p>
                  </div>
                </div>
                <div className="p-4">
                  <p className="text-sm text-gray-600 line-clamp-2 mb-3">{userItem.bio || 'No bio yet'}</p>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleViewProfile(userItem.id)}
                      className="flex-1 py-2 text-sm bg-gray-100 text-[#0F172A] rounded-lg font-medium hover:bg-gray-200"
                    >
                      Profile
                    </button>
                    <button 
                      onClick={() => handleMessage(userItem)}
                      className="flex-1 py-2 text-sm bg-[#0F172A] text-white rounded-lg font-medium hover:bg-gray-800 flex items-center justify-center gap-1"
                    >
                      <MessageCircle size={14} />
                      Message
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NearbyPage;
