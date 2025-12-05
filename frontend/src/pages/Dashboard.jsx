import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalTrucks: 0,
    totalFreights: 0,
    activeFreights: 0,
    averagePrice: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [trucksRes, freightsRes] = await Promise.all([
        api.get('/trucks'),
        api.get('/freights')
      ]);

      const trucks = trucksRes.data || [];
      const freights = freightsRes.data || [];
      const activeFreights = freights.filter(f => f.status === 'active') || [];
      const avgPrice = freights.length > 0
        ? Math.round(freights.reduce((sum, f) => sum + (f.price || 0), 0) / freights.length)
        : 0;

      setStats({
        totalTrucks: trucks.length,
        totalFreights: freights.length,
        activeFreights: activeFreights.length,
        averagePrice: avgPrice
      });
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading dashboard...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">Mini-TMS Dashboard</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-8">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Trucks Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-500 text-sm font-medium">Total Trucks</div>
          <div className="text-3xl font-bold text-blue-600 mt-2">{stats.totalTrucks}</div>
          <button
            onClick={() => navigate('/trucks')}
            className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Manage Trucks →
          </button>
        </div>

        {/* Freights Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-500 text-sm font-medium">Total Freights</div>
          <div className="text-3xl font-bold text-green-600 mt-2">{stats.totalFreights}</div>
          <button
            onClick={() => navigate('/freights')}
            className="mt-4 text-green-600 hover:text-green-800 text-sm font-medium"
          >
            Search Freights →
          </button>
        </div>

        {/* Active Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-500 text-sm font-medium">Active Loads</div>
          <div className="text-3xl font-bold text-purple-600 mt-2">{stats.activeFreights}</div>
          <div className="mt-4 text-sm text-gray-600">
            Currently in transit
          </div>
        </div>

        {/* Average Price Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-gray-500 text-sm font-medium">Average Price</div>
          <div className="text-3xl font-bold text-orange-600 mt-2">€{stats.averagePrice}</div>
          <div className="mt-4 text-sm text-gray-600">
            Per freight
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/trucks')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium transition"
          >
            🚚 Manage Trucks
          </button>
          <button
            onClick={() => navigate('/freights')}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium transition"
          >
            📦 Search Freights
          </button>
          <button
            onClick={() => navigate('/gps')}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded font-medium transition"
          >
            📍 GPS Tracking
          </button>
          <button
            onClick={fetchStats}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded font-medium transition"
          >
            🔄 Refresh Stats
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg shadow p-6 mt-8">
        <h3 className="text-lg font-bold text-blue-900 mb-2">Welcome to Mini-TMS! 🎉</h3>
        <p className="text-blue-800">
          Transportation Management System with automatic freight search and GPS tracking.
          Start by adding your trucks and then search for available freights.
        </p>
      </div>
    </div>
  );
}
