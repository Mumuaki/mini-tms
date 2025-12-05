import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trucks API
export const trucksAPI = {
  list: () => api.get('/api/trucks'),
  get: (id) => api.get(`/api/trucks/${id}`),
  create: (data) => api.post('/api/trucks', data),
  update: (id, data) => api.patch(`/api/trucks/${id}`, data),
  delete: (id) => api.delete(`/api/trucks/${id}`),
  updateGPS: (id) => api.post(`/api/trucks/${id}/update-gps`),
};

// Freights API
export const freightsAPI = {
  list: (params) => api.get('/api/freights', { params }),
  get: (id) => api.get(`/api/freights/${id}`),
  scrape: (data) => api.post('/api/freights/scrape', data),
  delete: (id) => api.delete(`/api/freights/${id}`),
};

// GPS API
export const gpsAPI = {
  history: (truckId, limit = 100) => 
    api.get(`/api/gps/history/${truckId}`, { params: { limit } }),
  geocode: (lat, lon) => 
    api.post('/api/gps/geocode', { lat, lon }),
};

// Health
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
