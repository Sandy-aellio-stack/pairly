import api from './api';

/**
 * Fetch nearby users based on current location
 * @param {number} lat - User's latitude
 * @param {number} lng - User's longitude
 * @param {number} radiusKm - Search radius in kilometers (default: 5)
 * @param {number} limit - Maximum number of users to return (default: 50)
 */
export async function fetchNearbyUsers(lat, lng, radiusKm = 5, limit = 50) {
  const response = await api.get('/nearby', {
    params: {
      lat,
      lng,
      radius_km: radiusKm,
      limit
    }
  });
  return response.data;
}

export default {
  fetchNearbyUsers
};
