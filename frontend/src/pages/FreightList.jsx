import React, { useState } from 'react';
import { useFreights } from '../hooks/useFreights';
import { useTrucks } from '../hooks/useTrucks';

export default function FreightList() {
  const { freights, loading, error, scrapeFreights } = useFreights();
  const { trucks } = useTrucks();
  
  const [filters, setFilters] = useState({
    origin: '',
    destination: '',
    loadingDateFrom: '',
    loadingDateTo: '',
    truckId: null,
  });
  const [scraping, setScraping] = useState(false);

  const handleScrape = async (e) => {
    e.preventDefault();
    setScraping(true);
    try {
      // Use truck's location as origin if selected and no origin provided
      let scrapeData = { ...filters };
      if (filters.truckId && !filters.origin) {
        const truck = trucks.find(t => t.id === parseInt(filters.truckId));
        if (truck?.lastKnownLocation) {
          scrapeData.origin = truck.lastKnownLocation;
        }
      }
      await scrapeFreights(scrapeData);
    } finally {
      setScraping(false);
    }
  };

  if (loading) return <div className="text-center py-8">Loading freights...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;

  return (
    <div>
      <h2 className="text-3xl font-bold mb-6">📦 Available Freights</h2>

      <div className="bg-white p-6 rounded shadow mb-6">
        <h3 className="text-lg font-bold mb-4">🔍 Search & Scrape</h3>
        <form onSubmit={handleScrape} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Origin (e.g., SK, 93101)"
              value={filters.origin}
              onChange={(e) => setFilters({ ...filters, origin: e.target.value })}
              className="border px-3 py-2 rounded"
            />
            <input
              type="text"
              placeholder="Destination"
              value={filters.destination}
              onChange={(e) => setFilters({ ...filters, destination: e.target.value })}
              required
              className="border px-3 py-2 rounded"
            />
            <select
              value={filters.truckId || ''}
              onChange={(e) => setFilters({ ...filters, truckId: e.target.value })}
              className="border px-3 py-2 rounded"
            >
              <option value="">Use GPS from Truck?</option>
              {trucks.map(t => (
                <option key={t.id} value={t.id}>
                  {t.licensePlate} ({t.lastKnownLocation || 'No GPS'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <input
              type="date"
              value={filters.loadingDateFrom}
              onChange={(e) => setFilters({ ...filters, loadingDateFrom: e.target.value })}
              className="border px-3 py-2 rounded"
            />
            <input
              type="date"
              value={filters.loadingDateTo}
              onChange={(e) => setFilters({ ...filters, loadingDateTo: e.target.value })}
              className="border px-3 py-2 rounded"
            />
          </div>

          <button
            type="submit"
            disabled={scraping}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {scraping ? '⏳ Scraping Trans.eu...' : '🚀 Start Scraper'}
          </button>
        </form>
      </div>

      <div className="space-y-4">
        {freights.length > 0 ? (
          freights.map(freight => (
            <div key={freight.id} className="bg-white p-4 rounded shadow hover:shadow-lg transition">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="font-bold">📍 {freight.loadingPlace} → {freight.unloadingPlace}</p>
                  <p className="text-sm text-gray-600">Loading: {freight.dateLoading}</p>
                  <p className="text-sm text-gray-600">Weight: {freight.weight} tons</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-green-600">€{freight.price}</p>
                  <p className="text-sm text-gray-600">{freight.bodyType}</p>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12 bg-gray-50 rounded">
            <p className="text-gray-600">No freights found. Start a scrape to load data!</p>
          </div>
        )}
      </div>
    </div>
  );
}
