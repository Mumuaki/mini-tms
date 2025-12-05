import { useState, useEffect } from 'react';
import { trucksAPI } from '../services/api';

export function useTrucks() {
  const [trucks, setTrucks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTrucks = async () => {
    setLoading(true);
    try {
      const response = await trucksAPI.list();
      setTrucks(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addTruck = async (truckData) => {
    try {
      const response = await trucksAPI.create(truckData);
      setTrucks([...trucks, response.data]);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updateTruck = async (id, truckData) => {
    try {
      const response = await trucksAPI.update(id, truckData);
      setTrucks(trucks.map(t => t.id === id ? response.data : t));
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const deleteTruck = async (id) => {
    try {
      await trucksAPI.delete(id);
      setTrucks(trucks.filter(t => t.id !== id));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const updateGPS = async (id) => {
    try {
      await trucksAPI.updateGPS(id);
      // Refetch truck to get updated GPS
      const response = await trucksAPI.get(id);
      setTrucks(trucks.map(t => t.id === id ? response.data : t));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  useEffect(() => {
    fetchTrucks();
  }, []);

  return { trucks, loading, error, addTruck, updateTruck, deleteTruck, updateGPS };
}
