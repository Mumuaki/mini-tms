import React, { useEffect, useState } from 'react';
import { freightService } from '../services/api';
import { Play, RefreshCw, MapPin, Calendar, DollarSign, Truck } from 'lucide-react';
import clsx from 'clsx';

const FreightList = () => {
    const [freights, setFreights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [scraping, setScraping] = useState(false);
    const [error, setError] = useState(null);

    // Filter states
    const [filters, setFilters] = useState({
        origin: '',
        destination: '',
        loading_date_from: '',
        loading_date_to: '',
        unloading_date_from: '',
        unloading_date_to: ''
    });

    const fetchFreights = async () => {
        try {
            setLoading(true);
            const data = await freightService.getAll();
            setFreights(data);
        } catch (err) {
            setError('Failed to load freights');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFreights();

        // Check if there's a saved truck location
        const savedLocation = localStorage.getItem('truck_location');
        if (savedLocation) {
            setFilters(prev => ({ ...prev, origin: savedLocation }));
            localStorage.removeItem('truck_location'); // Clear after using
        }
    }, []);

    const handleScrape = async () => {
        try {
            setScraping(true);
            setError(null);

            // Send filters to scraper
            await freightService.scrape(
                filters.origin || null,
                filters.destination || null,
                false,
                filters.loading_date_from || null,
                filters.loading_date_to || null,
                filters.unloading_date_from || null,
                filters.unloading_date_to || null
            );

            // Auto-refresh after 10 seconds to give scraper time to complete
            setTimeout(() => {
                fetchFreights();
                setScraping(false);
            }, 10000);
        } catch (err) {
            setError('Scraping failed to start');
            console.error(err);
            setScraping(false);
        }
    };

    const handleLaunchBrowser = async () => {
        try {
            await freightService.launchBrowser();
            console.log('Browser launched successfully');
        } catch (err) {
            setError('Failed to launch browser');
            console.error(err);
        }
    };

    if (loading && freights.length === 0) {
        return (
            <div className="flex justify-center items-center h-64">
                <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Freight Exchange</h1>
                    <p className="text-gray-500 mt-1">Manage and view available freights</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleLaunchBrowser}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors"
                    >
                        <Play className="w-4 h-4" />
                        Open Browser
                    </button>
                    <button
                        onClick={fetchFreights}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                    >
                        <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
                        Refresh
                    </button>
                    <button
                        onClick={handleScrape}
                        disabled={scraping}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Play className="w-4 h-4" />
                        {scraping ? 'Scraping...' : 'Start Scraper'}
                    </button>
                </div>
            </div>

            {/* Filter Form */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Search Filters</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Origin (Leave empty for GPS)
                        </label>
                        <input
                            type="text"
                            value={filters.origin}
                            onChange={(e) => setFilters({ ...filters, origin: e.target.value })}
                            placeholder="e.g. SK, 82106 or PL, Warsaw"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <p className="text-xs text-gray-500 mt-1">Format: CC, ZIP or CC, City</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Destination
                        </label>
                        <input
                            type="text"
                            value={filters.destination}
                            onChange={(e) => setFilters({ ...filters, destination: e.target.value })}
                            placeholder="e.g. DE, 10115 or DE, Berlin"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                        <p className="text-xs text-gray-500 mt-1">Format: CC, ZIP or CC, City</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Loading Date From
                        </label>
                        <input
                            type="date"
                            value={filters.loading_date_from}
                            onChange={(e) => setFilters({ ...filters, loading_date_from: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Loading Date To
                        </label>
                        <input
                            type="date"
                            value={filters.loading_date_to}
                            onChange={(e) => setFilters({ ...filters, loading_date_to: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Unloading Date From
                        </label>
                        <input
                            type="date"
                            value={filters.unloading_date_from}
                            onChange={(e) => setFilters({ ...filters, unloading_date_from: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Unloading Date To
                        </label>
                        <input
                            type="date"
                            value={filters.unloading_date_to}
                            onChange={(e) => setFilters({ ...filters, unloading_date_to: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4 font-semibold text-gray-900">Route</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Distance</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Dates</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Cargo</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Price</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {freights.map((freight) => (
                                <tr key={freight.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="space-y-1">
                                            <div className="flex items-center gap-2 text-gray-900 font-medium">
                                                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                                {freight.loading_place}
                                            </div>
                                            <div className="flex items-center gap-2 text-gray-900 font-medium">
                                                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                                                {freight.unloading_place}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2 text-gray-600">
                                            <MapPin className="w-4 h-4 text-gray-400" />
                                            {freight.distance_km ? `${freight.distance_km} km` : '-'}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="space-y-1 text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-4 h-4 text-gray-400" />
                                                {freight.loading_date ? new Date(freight.loading_date).toLocaleDateString() : '-'}
                                            </div>
                                            {freight.unloading_date && (
                                                <div className="flex items-center gap-2">
                                                    <Calendar className="w-4 h-4 text-gray-400" />
                                                    {new Date(freight.unloading_date).toLocaleDateString()}
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-start gap-2 text-gray-600">
                                            <Truck className="w-4 h-4 text-gray-400 mt-0.5" />
                                            <span className="max-w-xs truncate" title={freight.cargo_info}>
                                                {freight.cargo_info || '-'}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        {freight.price_original ? (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
                                                {freight.price_original} {freight.currency}
                                            </span>
                                        ) : (
                                            <span className="text-gray-400">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={clsx(
                                            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                                            freight.is_deal
                                                ? "bg-purple-100 text-purple-800"
                                                : "bg-blue-100 text-blue-800"
                                        )}>
                                            {freight.is_deal ? 'Deal' : 'New'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {freights.length === 0 && !loading && (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                        No freights found. Try running the scraper.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default FreightList;
