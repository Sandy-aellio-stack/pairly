/* eslint-disable react-hooks/exhaustive-deps */

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const userIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/149/149071.png",
  iconSize: [38, 38],
  iconAnchor: [19, 38],
});

const nearbyIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/1946/1946429.png",
  iconSize: [34, 34],
  iconAnchor: [17, 34],
});

export default function SnapMap() {
  const [userLocation, setUserLocation] = useState(null);
  const [nearbyUsers, setNearbyUsers] = useState([]);

  // ✅ Get precise user location
  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
      },
      (err) => {
        console.error("Location error:", err);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }
    );
  }, []);

  // ✅ Mock nearby users (replace with backend later)
  useEffect(() => {
    if (!userLocation) return;

    setNearbyUsers([
      {
        id: 1,
        name: "Ava",
        lat: userLocation.lat + 0.002,
        lng: userLocation.lng + 0.0015,
      },
      {
        id: 2,
        name: "Leo",
        lat: userLocation.lat - 0.0015,
        lng: userLocation.lng - 0.002,
      },
    ]);
  }, [userLocation]);

  if (!userLocation) {
    return (
      <div className="flex items-center justify-center h-screen">
        📍 Fetching your location…
      </div>
    );
  }

  return (
    <div className="h-screen w-full">
      <MapContainer
        center={[userLocation.lat, userLocation.lng]}
        zoom={15}
        scrollWheelZoom
        className="h-full w-full"
      >
        {/* ✅ Clean, high-contrast map */}
        <TileLayer
          attribution="© OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* ✅ User marker */}
        <Marker
          position={[userLocation.lat, userLocation.lng]}
          icon={userIcon}
        >
          <Popup>You are here</Popup>
        </Marker>

        {/* ✅ Accuracy radius */}
        <Circle
          center={[userLocation.lat, userLocation.lng]}
          radius={userLocation.accuracy}
          pathOptions={{ color: "#7c3aed", fillOpacity: 0.15 }}
        />

        {/* ✅ Nearby users */}
        {nearbyUsers.map((u) => (
          <Marker key={u.id} position={[u.lat, u.lng]} icon={nearbyIcon}>
            <Popup>
              <div className="text-sm font-medium">{u.name}</div>
              <button className="mt-2 text-violet-600 underline text-xs">
                View Profile
              </button>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
