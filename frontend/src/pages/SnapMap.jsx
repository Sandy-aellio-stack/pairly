import { MapContainer, TileLayer, Marker, Circle, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import MainLayout from "@/layouts/MainLayout";
import { updateLocation } from "@/services/location";
import { fetchNearbyUsers } from "@/services/nearby";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useNavigate } from "react-router-dom";
import { Users, MapPin, MessageSquare, RefreshCw, Crown, Lock, Sparkles } from "lucide-react";

// Custom user marker
const userIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/847/847969.png",
  iconSize: [38, 38],
  iconAnchor: [19, 38],
});

// Create custom icon for nearby users
const createNearbyUserIcon = (avatarUrl, isOnline = false) => {
  return L.divIcon({
    className: "custom-marker",
    html: `
      <div class="relative">
        <div class="w-10 h-10 rounded-full border-2 ${isOnline ? 'border-green-500' : 'border-gray-300'} overflow-hidden shadow-lg bg-white">
          <img src="${avatarUrl || 'https://i.pravatar.cc/100'}" class="w-full h-full object-cover" onerror="this.src='https://i.pravatar.cc/100'" />
        </div>
        ${isOnline ? '<div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>' : ''}
      </div>
    `,
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
  });
};

export default function SnapMap() {
  const [position, setPosition] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [nearbyUsers, setNearbyUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [useMockData, setUseMockData] = useState(false);
  const [hasSubscription] = useState(false);
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);
  const navigate = useNavigate();

  // Mock users fallback
  const mockUsers = [
    { id: 1, name: "Emma Wilson", avatar: "https://i.pravatar.cc/100?img=5", distance: 300, isOnline: true, isCreator: true, bio: "Travel & Lifestyle ✨", lat: 0, lng: 0 },
    { id: 2, name: "Jake Smith", avatar: "https://i.pravatar.cc/100?img=8", distance: 500, isOnline: true, isCreator: false, bio: "Coffee enthusiast ☕", lat: 0, lng: 0 },
    { id: 3, name: "Sophia Chen", avatar: "https://i.pravatar.cc/100?img=9", distance: 800, isOnline: true, isCreator: true, bio: "Fitness & Wellness 💪", lat: 0, lng: 0 },
    { id: 4, name: "Lucas Brown", avatar: "https://i.pravatar.cc/100?img=12", distance: 1200, isOnline: false, isCreator: false, bio: "Music lover 🎵", lat: 0, lng: 0 },
    { id: 5, name: "Mia Johnson", avatar: "https://i.pravatar.cc/100?img=16", distance: 1500, isOnline: true, isCreator: true, bio: "Art & Design 🎨", lat: 0, lng: 0 },
  ];

  // Load nearby users from API
  const loadNearbyUsers = async (lat, lng) => {
    try {
      const response = await fetchNearbyUsers(lat, lng, 5, 50);
      if (response.users && response.users.length > 0) {
        const users = response.users.map(u => ({
          id: u.user_id,
          name: u.display_name || "Unknown",
          avatar: u.avatar || `https://i.pravatar.cc/100?u=${u.user_id}`,
          distance: u.distance,
          isOnline: u.is_online || false,
          isCreator: false,
          bio: u.bio || "",
          lat: u.lat,
          lng: u.lng,
        }));
        setNearbyUsers(users);
        setUseMockData(false);
      } else {
        // No users from API, use mock with random positions near user
        const usersWithPositions = mockUsers.map((u, i) => ({
          ...u,
          lat: lat + (Math.random() - 0.5) * 0.01,
          lng: lng + (Math.random() - 0.5) * 0.01,
        }));
        setNearbyUsers(usersWithPositions);
        setUseMockData(true);
      }
    } catch (error) {
      console.log("Failed to fetch nearby users:", error);
      // Use mock with random positions
      const usersWithPositions = mockUsers.map((u, i) => ({
        ...u,
        lat: lat + (Math.random() - 0.5) * 0.01,
        lng: lng + (Math.random() - 0.5) * 0.01,
      }));
      setNearbyUsers(usersWithPositions);
      setUseMockData(true);
    }
  };

  // Get user location
  useEffect(() => {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        setPosition([lat, lng]);
        setAccuracy(pos.coords.accuracy);

        // Update location on backend
        try {
          await updateLocation(lat, lng);
        } catch (error) {
          console.log("Failed to update location:", error);
        }

        // Fetch nearby users
        await loadNearbyUsers(lat, lng);
      },
      (err) => console.error(err),
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRefresh = async () => {
    if (!position) return;
    setIsLoading(true);
    await loadNearbyUsers(position[0], position[1]);
    setIsLoading(false);
  };

  const handleUserClick = (user) => {
    setSelectedUser(user);
  };

  const handleMessage = () => {
    if (!hasSubscription) {
      setShowSubscribeModal(true);
    } else {
      navigate(`/messages/${selectedUser.id}`);
    }
  };

  const formatDistance = (meters) => {
    if (meters < 1000) return `${Math.round(meters)} m`;
    return `${(meters / 1000).toFixed(1)} km`;
  };

  if (!position) {
    return (
      <MainLayout>
        <div className="h-[calc(100vh-120px)] flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-4 animate-pulse">
              <MapPin className="h-8 w-8 text-violet-600" />
            </div>
            <p className="text-lg font-medium text-slate-700">📍 Getting your precise location…</p>
            <p className="text-sm text-slate-500 mt-2">Please allow location access</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="-mx-4 sm:-mx-6 lg:-mx-8 -mt-6">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between sticky top-0 z-[1001]">
          <div className="flex items-center gap-2">
            <MapPin className="h-6 w-6 text-violet-600" />
            <h1 className="text-xl font-bold text-slate-900">Snap Map</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1 border-slate-300">
              <Users className="h-3 w-3" />
              {nearbyUsers.filter(u => u.isOnline).length} nearby
            </Badge>
            {useMockData && (
              <Badge variant="secondary" className="bg-amber-100 text-amber-700">
                Demo
              </Badge>
            )}
            <Button size="icon" variant="ghost" onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Map */}
        <div className="relative h-[calc(100vh-240px)]">
          <MapContainer
            center={position}
            zoom={16}
            className="h-full w-full"
            zoomControl={false}
          >
            {/* Clean Light Map (Carto) */}
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              attribution="© OpenStreetMap © CARTO"
            />

            {/* Accuracy Circle */}
            <Circle
              center={position}
              radius={accuracy}
              pathOptions={{
                color: "#8b5cf6",
                fillColor: "#c4b5fd",
                fillOpacity: 0.35,
              }}
            />

            {/* User Marker */}
            <Marker position={position} icon={userIcon}>
              <Popup>You are here</Popup>
            </Marker>

            {/* Nearby Users Markers */}
            {nearbyUsers.map((user) => (
              user.lat && user.lng && (
                <Marker
                  key={user.id}
                  position={[user.lat, user.lng]}
                  icon={createNearbyUserIcon(user.avatar, user.isOnline)}
                  eventHandlers={{
                    click: () => handleUserClick(user),
                  }}
                />
              )
            ))}
          </MapContainer>
        </div>

        {/* Bottom User List */}
        <div className="bg-white border-t border-slate-200">
          <div className="p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-slate-900">
              <Users className="h-4 w-4 text-violet-600" />
              People Nearby
            </h3>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
              {nearbyUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex-shrink-0 cursor-pointer"
                  onClick={() => handleUserClick(user)}
                >
                  <div className="relative">
                    <Avatar className="h-14 w-14 border-2 border-white shadow">
                      <AvatarImage src={user.avatar} />
                      <AvatarFallback>{user.name[0]}</AvatarFallback>
                    </Avatar>
                    {user.isOnline && (
                      <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                    )}
                  </div>
                  <p className="text-xs text-center mt-1 truncate w-14">{user.name.split(" ")[0]}</p>
                  <p className="text-xs text-center text-gray-500">{formatDistance(user.distance)}</p>
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
                    <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                      <MapPin className="h-3 w-3" />
                      {formatDistance(selectedUser.distance)} away
                    </div>
                  </div>
                </div>
                <p className="text-gray-600 mt-2">{selectedUser.bio}</p>
                <div className="flex gap-3 mt-4">
                  <Button
                    className="flex-1 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                    onClick={handleMessage}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Message
                  </Button>
                  <Button 
                    variant="outline" 
                    className="flex-1 border-slate-300" 
                    onClick={() => navigate(`/profile/${selectedUser.id}`)}
                  >
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
              <h3 className="text-2xl font-bold mb-2 text-slate-900">Unlock Map Interactions</h3>
              <p className="text-base text-slate-600">
                Subscribe to message and interact with people you discover on the map.
              </p>
              <div className="mt-6 space-y-3">
                <Button
                  className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700"
                  onClick={() => navigate("/pricing")}
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
}
