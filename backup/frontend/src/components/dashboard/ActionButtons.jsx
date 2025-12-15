import React from 'react';

const ActionButtons = ({ onOpenBrowser, onScrapeFromGps, onScrapeWithFilters, isScraping }) => {
  return (
    <div className="flex items-center gap-4">
      <button
        onClick={onOpenBrowser}
        className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
      >
        1. Open Browser
      </button>
      <button
        onClick={onScrapeFromGps}
        disabled={isScraping}
        className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
      >
        {isScraping ? 'Scraping...' : '2. Scrape from Truck GPS'}
      </button>
      <button
        onClick={onScrapeWithFilters}
        disabled={isScraping}
        className="bg-gray-700 hover:bg-gray-800 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50"
      >
        {isScraping ? 'Scraping...' : 'Scrape with Manual Filters'}
      </button>
    </div>
  );
};

export default ActionButtons;
