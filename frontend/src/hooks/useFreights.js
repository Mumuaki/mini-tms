import { useState, useEffect } from 'react';
import { freightsAPI } from '../services/api';

export function useFreights() {
  const [freights, setFreights] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFreights = async (filters = {}) => {
    setLoading(true);
    try {
      const response = await freightsAPI.list(filters);
      setFreights(response.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const scrapeFreights = async (scrapeData) => {
    setLoading(true);
    try {
      const response = await freightsAPI.scrape(scrapeData);
      // Refetch after a delay to get results
      setTimeout(() => fetchFreights(), 5000);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteFreight = async (id) => {
    try {
      await freightsAPI.delete(id);
      setFreights(freights.filter(f => f.id !== id));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  useEffect(() => {
    fetchFreights();
  }, []);

  return { freights, loading, error, scrapeFreights, deleteFreight, fetchFreights };
}
