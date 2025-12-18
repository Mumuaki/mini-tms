import axios from 'axios';

<<<<<<< HEAD
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
=======
const api = axios.create({
    baseURL: '/api', // All requests will be proxied by Nginx
    headers: {
        'Content-Type': 'application/json',
    },
});

export const freightService = {
    getAll: async (skip = 0, limit = 100, showHidden = false) => {
        const response = await api.get('/freights', {
            params: { skip, limit, show_hidden: showHidden },
        });
        return response.data;
    },

    getById: async (id) => {
        const response = await api.get(`/freights/${id}`);
        return response.data;
    },

    update: async (id, data) => {
        const response = await api.patch(`/freights/${id}`, data);
        return response.data;
    },

    delete: async (id) => {
        const response = await api.delete(`/freights/${id}`);
        return response.data;
    },

    scrape: async (origin, destination, headless = true, loading_date_from, loading_date_to, unloading_date_from, unloading_date_to) => {
        // Convert dates from YYYY-MM-DD to DD.MM.YYYY
        const formatDate = (dateStr) => {
            if (!dateStr) return null;
            const [year, month, day] = dateStr.split('-');
            return `${day}.${month}.${year}`;
        };

        const response = await api.post('/freights/scrape', {
            origin,
            destination,
            headless,
            loading_date_from: formatDate(loading_date_from),
            loading_date_to: formatDate(loading_date_to),
            unloading_date_from: formatDate(unloading_date_from),
            unloading_date_to: formatDate(unloading_date_to)
        });
        return response.data;
    },

    launchBrowser: async () => {
        const response = await api.post('/scraper/launch');
        return response.data;
    },

    getTruckLocation: async (truckId) => {
        const response = await api.get(`/trucks/${truckId}/location`);
        return response.data;
    }
};

export const truckService = {
    getAll: async () => {
        const response = await api.get('/trucks');
        return response.data;
    },
    create: async (truckData) => {
        const response = await api.post('/trucks', truckData);
        return response.data;
    },
    update: async (truckId, truckData) => {
        const response = await api.patch(`/trucks/${truckId}`, truckData);
        return response.data;
    },
    delete: async (truckId) => {
        const response = await api.delete(`/trucks/${truckId}`);
        return response.data;
    },
    updateGps: async (truckId) => {
        const response = await api.post(`/trucks/${truckId}/update-gps`);
        return response.data;
    }
>>>>>>> 97953c3 (Initial commit from Specify template)
};

export default api;
