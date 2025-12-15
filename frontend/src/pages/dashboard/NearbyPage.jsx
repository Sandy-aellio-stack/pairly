import { useState, useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { RefreshCw, MessageCircle, MapPin, Navigation, X } from 'lucide-react';
import { locationAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';

const NearbyPage = () => {
  const navigate = useNavigate();
  const { credits } = useAuthStore();
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const [position, setPosition] = useState(null);
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    getLocation();
  }, []);

  useEffect(() => {
    if (position && mapContainer.current && !mapRef.current) {
      initMap();
    }
  }, [position]);

  useEffect(() => {
    if (mapRef.current && nearbyUsers.length > 0) {
      addMarkers();
    }
  }, [nearbyUsers]);

  const initMap = () => {
    mapRef.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [position[1], position[0]],
      zoom: 13,
    });

    mapRef.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Add user marker
    const userEl = document.createElement('div');
    userEl.className = 'user-marker';
    userEl.innerHTML = `
      <div class="w-12 h-12 rounded-full bg-purple-500 border-4 border-white shadow-lg flex items-center justify-center animate-pulse-purple">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
        </svg>
      </div>
    `;
    new maplibregl.Marker({ element: userEl })
      .setLngLat([position[1], position[0]])
      .addTo(mapRef.current);
  };

  const addMarkers = () => {
    // Clear existing markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    nearbyUsers.forEach((user, i) => {
      // Generate position around user
      const offsetLat = (Math.random() - 0.5) * 0.02;
      const offsetLng = (Math.random() - 0.5) * 0.02;
      const lat = position[0] + offsetLat;
      const lng = position[1] + offsetLng;

      const el = document.createElement('div');
      el.className = 'nearby-marker cursor-pointer';
      el.innerHTML = `
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 border-3 border-white shadow-lg flex items-center justify-center text-white font-bold text-sm">
          ${user.name?.[0] || '?'}
        </div>
      `;
      el.onclick = () => setSelectedUser(user);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([lng, lat])
        .addTo(mapRef.current);
      
      markersRef.current.push(marker);
    });
  };

  const getLocation = () => {
    if (!navigator.geolocation) {
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        setPosition([latitude, longitude]);
        
        try {
          await locationAPI.update(latitude, longitude);
          const response = await locationAPI.getNearby(latitude, longitude, 50);
          setNearbyUsers(response.data.users || []);
        } catch (e) {
          // Mock data for demo
          const mockUsers = [
            { id: '1', name: 'Sarah', age: 24, distance_km: 2.5, bio: 'Coffee lover ☕', is_online: true },
            { id: '2', name: 'Emma', age: 26, distance_km: 3.1, bio: 'Travel enthusiast ✈️', is_online: true },
            { id: '3', name: 'Mia', age: 23, distance_km: 4.2, bio: 'Yoga & meditation 🧘', is_online: false },
            { id: '4', name: 'Ava', age: 25, distance_km: 5.0, bio: 'Art & music 🎨', is_online: true },
          ];
          setNearbyUsers(mockUsers);
        } finally {
          setLoading(false);
        }
      },
      () => {
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  const handleRefresh = () => {
    setLoading(true);
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }
    getLocation();
  };

  const handleMessage = (userId) => {
    if (credits < 1) {
      navigate('/dashboard/credits');
      return;
    }
    navigate(`/dashboard/chat/${userId}`);
  };

  if (loading) {
    return (
      <div className="h-[calc(100vh-200px)] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Navigation size={32} className="text-purple-500" />
          </div>
          <p className="text-gray-500">📍 Getting your location...</p>
        </div>
      </div>
    );
  }

  if (!position) {
    return (
      <div className="h-[calc(100vh-200px)] flex items-center justify-center">
        <div className="text-center card max-w-md p-8">
          <MapPin size={48} className="text-purple-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Location Required</h2>
          <p className="text-gray-500 mb-6">
            Please enable location access to discover nearby people.
          </p>
          <button onClick={handleRefresh} className="btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-200px)] lg:h-[calc(100vh-100px)] relative rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
        <div className="bg-white/90 backdrop-blur-lg rounded-full px-4 py-2 flex items-center gap-2 shadow-lg">
          <MapPin size={16} className="text-purple-500" />
          <span className="text-sm font-medium text-gray-700">{nearbyUsers.length} people nearby</span>
        </div>
        <button
          onClick={handleRefresh}
          className="bg-white/90 backdrop-blur-lg rounded-full p-3 hover:bg-purple-50 transition-colors shadow-lg"
        >
          <RefreshCw size={20} className={`text-gray-600 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Map */}
      <div ref={mapContainer} className="h-full w-full" />

      {/* User list */}
      <div className="absolute bottom-4 left-4 right-4 z-10">
        <div className="bg-white/95 backdrop-blur-lg rounded-2xl shadow-xl p-4 max-h-48 overflow-y-auto">
          <h3 className="font-semibold mb-3 text-sm text-gray-500">People Nearby</h3>
          {nearbyUsers.length === 0 ? (
            <p className="text-gray-400 text-sm">No one nearby yet. Try expanding your search radius.</p>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-2">
              {nearbyUsers.map((user, i) => (
                <div
                  key={user.id}
                  onClick={() => setSelectedUser(user)}
                  className="flex-shrink-0 text-center cursor-pointer profile-card"
                >
                  <div className={`w-14 h-14 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center mb-1 border-2 border-transparent hover:border-purple-500 transition-colors shadow-md`}>
                    <span className="text-xl font-bold text-white">{user.name?.[0]}</span>
                  </div>
                  <p className="text-xs text-gray-700 truncate w-14">{user.name?.split(' ')[0]}</p>
                  <p className="text-xs text-purple-500 font-medium">{user.distance_km}km</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Selected user modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedUser(null)} />
          <div className="relative bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl">
            <button
              onClick={() => setSelectedUser(null)}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:bg-gray-200"
            >
              <X size={18} />
            </button>
            <div className="text-center">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center mx-auto mb-4 shadow-xl">
                <span className="text-3xl font-bold text-white">{selectedUser.name?.[0]}</span>
              </div>
              <h3 className="text-xl font-bold text-gray-900">{selectedUser.name}</h3>
              <p className="text-gray-500">{selectedUser.age} • {selectedUser.distance_km}km away</p>
              {selectedUser.is_online && (
                <span className="inline-flex items-center gap-1 text-green-500 text-sm mt-1">
                  <span className="w-2 h-2 rounded-full bg-green-500" /> Online
                </span>
              )}
              {selectedUser.bio && (
                <p className="text-gray-600 mt-3 text-sm">{selectedUser.bio}</p>
              )}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setSelectedUser(null)}
                  className="btn-ghost flex-1"
                >
                  Close
                </button>
                <button
                  onClick={() => handleMessage(selectedUser.id)}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  <MessageCircle size={18} />
                  Message
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NearbyPage;
