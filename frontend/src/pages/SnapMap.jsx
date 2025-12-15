import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Globe, MapPin, Navigation, Users, X, MessageSquare,
  Crown, Lock, Sparkles, RefreshCw, ZoomIn, ZoomOut, Locate
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { updateLocation } from '@/services/location';
import { fetchNearbyUsers } from '@/services/nearby';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (imageUrl, isOnline = true) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div class="relative">
        <div class="w-12 h-12 rounded-full border-3 ${isOnline ? 'border-green-500' : 'border-gray-400'} overflow-hidden shadow-lg bg-white">
          <img src="${imageUrl}" class="w-full h-full object-cover" />
        </div>
        ${isOnline ? '<div class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>' : ''}
      </div>
    `,
    iconSize: [48, 48],
    iconAnchor: [24, 48],
    popupAnchor: [0, -48],
  });
};

const MapControls = ({ onLocate, onZoomIn, onZoomOut, onRefresh }) => {
  return (
    <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
      <Button size="icon" variant="secondary" onClick={onLocate} className="shadow-lg">
        <Locate className="h-5 w-5" />
      </Button>
      <Button size="icon" variant="secondary" onClick={onZoomIn} className="shadow-lg">
        <ZoomIn className="h-5 w-5" />
      </Button>
      <Button size="icon" variant="secondary" onClick={onZoomOut} className="shadow-lg">
        <ZoomOut className="h-5 w-5" />
      </Button>
      <Button size="icon" variant="secondary" onClick={onRefresh} className="shadow-lg">
        <RefreshCw className="h-5 w-5" />
      </Button>
    </div>
  );
};

const MapController = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1 });
    }
  }, [center, zoom, map]);

  return null;
};

const SnapMap = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [userLocation, setUserLocation] = useState(null);
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);
  const [mapCenter, setMapCenter] = useState([40.7128, -74.0060]); // NYC default
  const [mapZoom, setMapZoom] = useState(13);
  const [isLoading, setIsLoading] = useState(true);
  const [hasSubscription, setHasSubscription] = useState(false); // Mock subscription status
  const [useMockData, setUseMockData] = useState(false); // Fallback to mock if API fails
  const mapRef = useRef(null);

  // Fetch nearby users from API or use mock data
  const loadNearbyUsers = async (lat, lng) => {
    try {
      const response = await fetchNearbyUsers(lat, lng, 5, 50);
      if (response.users && response.users.length > 0) {
        // Transform API response to component format
        const users = response.users.map(u => ({
          id: u.user_id,
          name: u.display_name || 'Unknown',
          username: u.display_name?.toLowerCase().replace(/\s+/g, '') || 'user',
          avatar: u.avatar || `https://i.pravatar.cc/100?u=${u.user_id}`,
          distance: u.distance_km < 1 
            ? `${Math.round(u.distance)} m` 
            : `${u.distance_km} km`,
          isOnline: u.is_online || false,
          isCreator: false,
          bio: u.bio || '',
          lat: u.lat,
          lng: u.lng,
        }));
        setNearbyUsers(users);
        setUseMockData(false);
      } else {
        // No users found, use mock data
        loadMockUsers();
      }
    } catch (error) {
      console.log('Failed to fetch nearby users, using mock data:', error);
      loadMockUsers();
    }
  };

  // Mock nearby users fallback
  const loadMockUsers = () => {
    setUseMockData(true);
    const mockUsers = [
      {
        id: 1,
        name: 'Emma Wilson',
        username: 'emmaw',
        avatar: 'https://i.pravatar.cc/100?img=5',
        distance: '0.3 mi',
        isOnline: true,
        isCreator: true,
        bio: 'Travel & Lifestyle ✨',
        lat: 40.7138,
        lng: -74.0050,
      },
      {
        id: 2,
        name: 'Jake Smith',
        username: 'jakes',
        avatar: 'https://i.pravatar.cc/100?img=8',
        distance: '0.5 mi',
        isOnline: true,
        isCreator: false,
        bio: 'Coffee enthusiast ☕',
        lat: 40.7148,
        lng: -74.0080,
      },
      {
        id: 3,
        name: 'Sophia Chen',
        username: 'sophiac',
        avatar: 'https://i.pravatar.cc/100?img=9',
        distance: '0.8 mi',
        isOnline: true,
        isCreator: true,
        bio: 'Fitness & Wellness 💪',
        lat: 40.7108,
        lng: -74.0020,
      },
      {
        id: 4,
        name: 'Lucas Brown',
        username: 'lucasb',
        avatar: 'https://i.pravatar.cc/100?img=12',
        distance: '1.2 mi',
        isOnline: false,
        isCreator: false,
        bio: 'Music lover 🎵',
        lat: 40.7168,
        lng: -74.0100,
      },
      {
        id: 5,
        name: 'Mia Johnson',
        username: 'miaj',
        avatar: 'https://i.pravatar.cc/100?img=16',
        distance: '1.5 mi',
        isOnline: true,
        isCreator: true,
        bio: 'Art & Design 🎨',
        lat: 40.7088,
        lng: -74.0090,
      },
    ];
    setNearbyUsers(mockUsers);
  };

  // Initial load
  useEffect(() => {
    // Load mock data initially while waiting for location
    loadMockUsers();
    setIsLoading(false);
  }, []);

  // Get user's location and update backend
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          setMapCenter([latitude, longitude]);
          
          // Update location on backend
          try {
            await updateLocation(latitude, longitude);
            console.log('Location updated on backend');
          } catch (error) {
            console.log('Failed to update location on backend:', error);
          }
          
          // Fetch nearby users
          await loadNearbyUsers(latitude, longitude);
        },
        (error) => {
          console.log('Location error:', error);
          toast.info('Using default location. Enable location for better experience.');
        }
      );
    }
  }, []);

  const handleUserClick = (nearbyUser) => {
    setSelectedUser(nearbyUser);
  };

  const handleInteract = () => {
    if (!hasSubscription) {
      setShowSubscribeModal(true);
    } else {
      navigate(`/messages/${selectedUser.id}`);
    }
  };

  const handleLocate = () => {
    if (userLocation) {
      setMapCenter([userLocation.lat, userLocation.lng]);
      setMapZoom(15);
    } else if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          setMapCenter([latitude, longitude]);
          setMapZoom(15);
        }
      );
    }
  };

  const handleZoomIn = () => setMapZoom(prev => Math.min(prev + 1, 18));
  const handleZoomOut = () => setMapZoom(prev => Math.max(prev - 1, 5));
  const handleRefresh = async () => {
    setIsLoading(true);
    if (userLocation) {
      await loadNearbyUsers(userLocation.lat, userLocation.lng);
    }
    setTimeout(() => setIsLoading(false), 500);
    toast.success('Map refreshed!');
  };

  return (
    <MainLayout>
      <div className="-mx-4 sm:-mx-6 lg:-mx-8 -mt-6">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between sticky top-0 z-[1001]">
          <div className="flex items-center gap-2">
            <Globe className="h-6 w-6 text-violet-600" />
            <h1 className="text-xl font-bold text-slate-900">Snap Map</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 border-slate-300">
              <Users className="h-3 w-3" />
              {nearbyUsers.filter(u => u.isOnline).length} nearby
            </Badge>
          </div>
        </div>

        {/* Map Container */}
        <div className="relative h-[calc(100vh-180px)]">
          <MapContainer
            center={mapCenter}
            zoom={mapZoom}
            className="h-full w-full"
            ref={mapRef}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapController center={mapCenter} zoom={mapZoom} />

            {/* User's location */}
            {userLocation && (
              <>
                <Circle
                  center={[userLocation.lat, userLocation.lng]}
                  radius={100}
                  pathOptions={{ color: '#7c3aed', fillColor: '#ede9fe', fillOpacity: 0.3 }}
                />
                <Marker
                  position={[userLocation.lat, userLocation.lng]}
                  icon={createCustomIcon('https://i.pravatar.cc/100?img=1', true)}
                >
                  <Popup>You are here</Popup>
                </Marker>
              </>
            )}

            {/* Nearby users */}
            {nearbyUsers.map((nearbyUser) => (
              <Marker
                key={nearbyUser.id}
                position={[nearbyUser.lat, nearbyUser.lng]}
                icon={createCustomIcon(nearbyUser.avatar, nearbyUser.isOnline)}
                eventHandlers={{
                  click: () => handleUserClick(nearbyUser),
                }}
              />
            ))}
          </MapContainer>

          {/* Map Controls */}
          <MapControls
            onLocate={handleLocate}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onRefresh={handleRefresh}
          />

          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-[1000]">
              <RefreshCw className="h-8 w-8 text-violet-600 animate-spin" />
            </div>
          )}
        </div>

        {/* Bottom User List */}
        <div className="bg-white border-t border-slate-200">
          <div className="p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-slate-900">
              <MapPin className="h-4 w-4 text-violet-600" />
              People Nearby
            </h3>
            <div className="flex gap-3 overflow-x-auto pb-2">
              {nearbyUsers.map((nearbyUser) => (
                <div
                  key={nearbyUser.id}
                  className="flex-shrink-0 cursor-pointer"
                  onClick={() => handleUserClick(nearbyUser)}
                >
                  <div className="relative">
                    <Avatar className="h-14 w-14 border-2 border-white shadow">
                      <AvatarImage src={nearbyUser.avatar} />
                      <AvatarFallback>{nearbyUser.name[0]}</AvatarFallback>
                    </Avatar>
                    {nearbyUser.isOnline && (
                      <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                    )}
                  </div>
                  <p className="text-xs text-center mt-1 truncate w-14">{nearbyUser.name.split(' ')[0]}</p>
                  <p className="text-xs text-center text-gray-500">{nearbyUser.distance}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Selected User Modal */}
        <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
          <DialogContent className="sm:max-w-md">
            {selectedUser && (
              <>
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Avatar className="h-20 w-20">
                      <AvatarImage src={selectedUser.avatar} />
                      <AvatarFallback>{selectedUser.name[0]}</AvatarFallback>
                    </Avatar>
                    {selectedUser.isOnline && (
                      <div className="absolute bottom-1 right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-xl font-bold">{selectedUser.name}</h3>
                      {selectedUser.isCreator && (
                        <Badge className="bg-gradient-to-r from-amber-500 to-pink-500 text-xs">
                          <Sparkles className="h-3 w-3 mr-1" />
                          Creator
                        </Badge>
                      )}
                    </div>
                    <p className="text-gray-500">@{selectedUser.username}</p>
                    <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                      <MapPin className="h-3 w-3" />
                      {selectedUser.distance} away
                    </div>
                  </div>
                </div>
                <p className="text-gray-600 mt-2">{selectedUser.bio}</p>
                <div className="flex gap-3 mt-4">
                  <Button
                    className="flex-1 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                    onClick={handleInteract}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Message
                  </Button>
                  <Button variant="outline" className="flex-1 border-slate-300" onClick={() => navigate(`/profile/${selectedUser.id}`)}>
                    View Profile
                  </Button>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>

        {/* Subscribe Modal */}
        <Dialog open={showSubscribeModal} onOpenChange={setShowSubscribeModal}>
          <DialogContent className="sm:max-w-md text-center">
            <div className="py-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-4">
                <Lock className="h-8 w-8 text-white" />
              </div>
              <DialogTitle className="text-2xl mb-2 text-slate-900">Unlock Map Interactions</DialogTitle>
              <DialogDescription className="text-base text-slate-600">
                Subscribe to message and interact with people you discover on the map.
              </DialogDescription>
              <div className="mt-6 space-y-3">
                <Button
                  className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                  onClick={() => navigate('/pricing')}
                >
                  <Crown className="h-4 w-4 mr-2" />
                  Subscribe Now
                </Button>
                <Button variant="outline" className="w-full border-slate-300" onClick={() => setShowSubscribeModal(false)}>
                  Maybe Later
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </MainLayout>
  );
};

export default SnapMap;
