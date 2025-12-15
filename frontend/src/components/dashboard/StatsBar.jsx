import React from 'react';

const StatCard = ({ title, value, children }) => (
  <div className="bg-white rounded-lg shadow p-4 transition-all hover:shadow-md hover:-translate-y-1">
    <div className="flex items-center">
      {children && <div className="mr-4">{children}</div>}
      <div>
        <div className="text-gray-500 text-sm">{title}</div>
        <div className="text-2xl font-bold text-gray-800">{value}</div>
      </div>
    </div>
  </div>
);

const StatsBar = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatCard title="Total Offers" value={stats.totalOffers || 0} />
      <StatCard title="Last Update" value={stats.lastUpdate || 'Never'} />
      <StatCard title="Status" value={stats.status || 'Idle'} />
      <StatCard title="Active Scraping" value={stats.scrapingStatus || 'No'} />
    </div>
  );
};

export default StatsBar;
