import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RefreshCw, MessageCircle, MapPin, Navigation } from 'lucide-react';
import { locationAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import { useNavigate } from 'react-router-dom';

// Custom icons
const userIcon = new L.Icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/149/149071.png',
  iconSize: [40, 40],
  iconAnchor: [20, 40],
});

const nearbyIcon = new L.Icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/1946/1946429.png',
  iconSize: [36, 36],
  iconAnchor: [18, 36],
});

// Map center controller
const MapController = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
};

const NearbyPage = () => {
  const navigate = useNavigate();
  const { credits } = useAuthStore();
  const [position, setPosition] = useState(null);
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    getLocation();
  }, []);

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
          // Update location on backend
          await locationAPI.update(latitude, longitude);
          // Get nearby users
          const response = await locationAPI.getNearby(latitude, longitude, 50);
          setNearbyUsers(response.data.users || []);
        } catch (e) {
          console.log('Failed to get nearby users');
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        console.error('Location error:', err);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  };

  const handleRefresh = () => {
    setLoading(true);
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
          <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Navigation size={32} className="text-purple-400" />
          </div>
          <p className="text-white/60">📍 Getting your location...</p>
        </div>
      </div>
    );
  }

  if (!position) {
    return (
      <div className="h-[calc(100vh-200px)] flex items-center justify-center">
        <div className="text-center card-dark max-w-md">
          <MapPin size={48} className="text-purple-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Location Required</h2>
          <p className="text-white/60 mb-6">
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
    <div className="h-[calc(100vh-200px)] lg:h-[calc(100vh-100px)] relative">
      {/* Header */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex items-center justify-between">
        <div className="bg-black/80 backdrop-blur-lg rounded-full px-4 py-2 flex items-center gap-2">
          <MapPin size={16} className="text-purple-400" />
          <span className="text-sm">{nearbyUsers.length} people nearby</span>
        </div>
        <button
          onClick={handleRefresh}
          className="bg-black/80 backdrop-blur-lg rounded-full p-3 hover:bg-purple-500/20 transition-colors"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Map */}
      <MapContainer
        center={position}
        zoom={14}
        className="h-full w-full rounded-2xl overflow-hidden"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; OpenStreetMap &copy; CARTO"
        />
        <MapController center={position} />

        {/* User marker */}
        <Marker position={position} icon={userIcon}>
          <Popup>You are here</Popup>
        </Marker>

        {/* Accuracy circle */}
        <Circle
          center={position}
          radius={100}
          pathOptions={{ color: '#7B5CFF', fillColor: '#7B5CFF', fillOpacity: 0.15 }}
        />

        {/* Nearby users */}
        {nearbyUsers.map((user) => (
          user.distance_km !== undefined && (
            <Marker
              key={user.id}
              position={[
                position[0] + (Math.random() - 0.5) * 0.02,
                position[1] + (Math.random() - 0.5) * 0.02
              ]}
              icon={nearbyIcon}
              eventHandlers={{
                click: () => setSelectedUser(user),
              }}
            />
          )
        ))}
      </MapContainer>

      {/* User list sidebar */}
      <div className="absolute bottom-4 left-4 right-4 z-[1000]">
        <div className="bg-black/90 backdrop-blur-lg rounded-2xl border border-white/10 p-4 max-h-48 overflow-y-auto">
          <h3 className="font-semibold mb-3 text-sm text-white/60">People Nearby</h3>
          {nearbyUsers.length === 0 ? (
            <p className="text-white/40 text-sm">No one nearby yet. Try expanding your search radius.</p>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-2">
              {nearbyUsers.map((user) => (
                <div
                  key={user.id}
                  onClick={() => setSelectedUser(user)}
                  className="flex-shrink-0 text-center cursor-pointer user-card"
                >
                  <div className="w-14 h-14 rounded-full bg-purple-500/20 flex items-center justify-center mb-1 border-2 border-transparent hover:border-purple-500 transition-colors">
                    {user.profile_pictures?.[0] ? (
                      <img src={user.profile_pictures[0]} alt="" className="w-full h-full object-cover rounded-full" />
                    ) : (
                      <span className="text-xl font-bold text-purple-400">{user.name?.[0]}</span>
                    )}
                  </div>
                  <p className="text-xs truncate w-14">{user.name?.split(' ')[0]}</p>
                  <p className="text-xs text-purple-400">{user.distance_km}km</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Selected user modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70" onClick={() => setSelectedUser(null)} />
          <div className="relative bg-[#0B0B0F] border border-white/10 rounded-3xl p-6 w-full max-w-sm">
            <div className="text-center">
              <div className="w-24 h-24 rounded-full bg-purple-500/20 flex items-center justify-center mx-auto mb-4">
                {selectedUser.profile_pictures?.[0] ? (
                  <img src={selectedUser.profile_pictures[0]} alt="" className="w-full h-full object-cover rounded-full" />
                ) : (
                  <span className="text-3xl font-bold text-purple-400">{selectedUser.name?.[0]}</span>
                )}
              </div>
              <h3 className="text-xl font-bold">{selectedUser.name}</h3>
              <p className="text-white/60">{selectedUser.age} • {selectedUser.distance_km}km away</p>
              {selectedUser.bio && (
                <p className="text-white/40 mt-2 text-sm">{selectedUser.bio}</p>
              )}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setSelectedUser(null)}
                  className="btn-secondary flex-1"
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
