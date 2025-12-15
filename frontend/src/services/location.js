import api from './api';

/**
 * Update user's current location
 */
export async function updateLocation(lat, lng) {
  const response = await api.post('/location/update', { lat, lng });
  return response.data;
}

/**
 * Toggle map visibility
 */
export async function updateVisibility(isVisibleOnMap) {
  const response = await api.post('/location/visibility', { is_visible_on_map: isVisibleOnMap });
  return response.data;
}

/**
 * Get current user's location
 */
export async function getMyLocation() {
  const response = await api.get('/location/me');
  return response.data;
}

export default {
  updateLocation,
  updateVisibility,
  getMyLocation
};
