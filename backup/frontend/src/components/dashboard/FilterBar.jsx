import React, { useState, useEffect } from 'react';

const FilterBar = ({ filters, onFilterChange }) => {

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onFilterChange(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <h3 className="text-lg font-semibold mb-2">Manual Filters</h3>
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="origin">Origin</label>
          <input
            type="text"
            id="origin"
            name="origin"
            value={filters.origin || ''}
            onChange={handleInputChange}
            placeholder="e.g. SK, 82106"
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="destination">Destination</label>
          <input
            type="text"
            id="destination"
            name="destination"
            value={filters.destination || ''}
            onChange={handleInputChange}
            placeholder="e.g. PL, Warsaw"
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div className="flex gap-2">
          <div className="flex flex-col">
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="loading_date_from">Load Date From</label>
            <input
              type="date"
              id="loading_date_from"
              name="loading_date_from"
              value={filters.loading_date_from || ''}
              onChange={handleInputChange}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="flex flex-col">
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="loading_date_to">To</label>
            <input
              type="date"
              id="loading_date_to"
              name="loading_date_to"
              value={filters.loading_date_to || ''}
              onChange={handleInputChange}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <p className="text-sm text-gray-500 self-end pb-2">
          Use these filters with the "Scrape with Manual Filters" button.
        </p>
      </div>
    </div>
  );
};

export default FilterBar;
