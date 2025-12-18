import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom'; // Import useLocation
import StatsBar from '../components/dashboard/StatsBar';
import FilterBar from '../components/dashboard/FilterBar';
import FreightTable from '../components/dashboard/FreightTable';
import ActionButtons from '../components/dashboard/ActionButtons';
import { freightService } from '../services/api';

const DashboardPage = () => {
  const location = useLocation(); // Use useLocation hook
  const [filters, setFilters] = useState({ origin: '', destination: '' });
  const [freights, setFreights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isScraping, setIsScraping] = useState(false);
  const [stats, setStats] = useState({
    totalOffers: 0,
    lastUpdate: 'Never',
    status: 'Idle',
    scrapingStatus: 'No'
  });

  // Effect to initialize filters from navigation state
  useEffect(() => {
    const state = location.state;
    if (state?.originFilter) {
      setFilters(prev => ({ ...prev, origin: state.originFilter }));
      // Automatically clear state but keep the filter
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (state?.truckId) {
      // If we came with a truckId but NO location, try to fetch it live
      // This implements "Find Loads" -> Get Live GPS
      fetchLiveTruckLocation(state.truckId);
    }
  }, [location.state]);

  const fetchLiveTruckLocation = async (truckId) => {
    try {
      setStats(prev => ({ ...prev, status: 'Fetching GPS...' }));
      // We need a service method for this, let's assume one exists or use raw axios for now to save time
      // Better to add to freightService in a real app
      const response = await freightService.getTruckLocation(truckId);
      if (response.address) {
        setFilters(prev => ({ ...prev, origin: response.address }));
        setStats(prev => ({ ...prev, status: 'GPS Found' }));
      }
    } catch (err) {
      console.error("Could not fetch truck location", err);
      alert("Could not fetch live location for this truck. Please check GPS settings.");
      setStats(prev => ({ ...prev, status: 'GPS Error' }));
    }
  };

  const fetchFreights = useCallback(async () => {
    try {
      setLoading(true);
      setStats(prev => ({ ...prev, status: 'Loading...' }));
      const data = await freightService.getAll();
      setFreights(data);
      setStats(prev => ({
        ...prev,
        totalOffers: data.length,
        lastUpdate: new Date().toLocaleString(),
        status: 'Ready',
      }));
    } catch (err) {
      console.error('Failed to load freights:', err);
      setStats(prev => ({ ...prev, status: 'Error' }));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFreights();
  }, [fetchFreights]);

  const handleOpenBrowser = async () => {
    try {
      await freightService.launchBrowser();
      alert('Browser launched successfully. Please log in to Trans.eu and navigate to the freight exchange page.');
    } catch (err) {
      alert('Failed to launch browser. Is the backend running?');
      console.error(err);
    }
  };

  const runScrape = async (scrapePayload) => {
    setIsScraping(true);
    setStats(prev => ({ ...prev, status: 'Scraping...', scrapingStatus: 'Yes' }));
    try {
      // freightService.scrape expects positional arguments:
      // origin, destination, headless, loading_date_from, loading_date_to, unloading_date_from, unloading_date_to
      await freightService.scrape(
        scrapePayload.origin || null,
        scrapePayload.destination || null,
        false, // headless (false to see what happens, or true for background) - let's default to false as requested previously for visibility
        scrapePayload.loading_date_from || null,
        scrapePayload.loading_date_to || null,
        scrapePayload.unloading_date_from || null,
        scrapePayload.unloading_date_to || null
      );

      // Give backend time to process
      setTimeout(() => {
        fetchFreights();
        setIsScraping(false);
        setStats(prev => ({ ...prev, status: 'Refreshed', scrapingStatus: 'No' }));
      }, 10000); // 10 second delay to allow scraper to finish
    } catch (err) {
      alert('Failed to start scraping task.');
      console.error(err);
      setIsScraping(false);
      setStats(prev => ({ ...prev, status: 'Error', scrapingStatus: 'No' }));
    }
  };

  const handleScrapeFromGps = () => {
    // Call scrape with null origin to trigger backend GPS logic
    runScrape({ origin: null, destination: filters.destination || null });
  };

  const handleScrapeWithFilters = () => {
    if (!filters.origin && !filters.destination) {
      alert('Please provide at least an origin or a destination for manual search.');
      return;
    }
    runScrape(filters);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <ActionButtons
          onOpenBrowser={handleOpenBrowser}
          onScrapeFromGps={handleScrapeFromGps}
          onScrapeWithFilters={handleScrapeWithFilters}
          isScraping={isScraping}
        />
      </div>
      <StatsBar stats={stats} />
      <FilterBar filters={filters} onFilterChange={setFilters} />
      <FreightTable freights={freights} loading={loading || isScraping} />
    </div>
  );
};

export default DashboardPage;

