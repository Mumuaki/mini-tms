import React from 'react';

// Simple Modal Component
const DetailsModal = ({ freight, onClose }) => {
  if (!freight) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div className="relative p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Freight Details</h3>
          <div className="space-y-3 text-sm text-gray-700">
            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Trans ID:</span>
              <span className="col-span-2">{freight.trans_id}</span>
            </div>
            {/* Extended Details */}
            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Body Type:</span>
              <span className="col-span-2">{freight.body_type || '-'}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Capacity/LDM:</span>
              <span className="col-span-2">{freight.capacity || '-'} / {freight.ldm || '-'}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Payment:</span>
              <span className="col-span-2">{freight.payment_terms || '-'}</span>
            </div>

            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Loading:</span>
              <span className="col-span-2">
                <div>{freight.loading_place}</div>
                <div className="text-gray-500">{freight.loading_date}</div>
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 border-b pb-2">
              <span className="font-semibold">Unloading:</span>
              <span className="col-span-2">
                <div>{freight.unloading_place}</div>
                <div className="text-gray-500">{freight.unloading_date}</div>
              </span>
            </div>

            <div className="border-b pb-2">
              <span className="font-semibold block mb-1">Additional Description:</span>
              <p className="bg-gray-50 p-2 rounded italic">{freight.additional_description || 'None'}</p>
            </div>

            {freight.raw_text && (
              <div>
                <span className="font-semibold block mb-1">Raw Scraped Text:</span>
                <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto whitespace-pre-wrap">
                  {freight.raw_text}
                </pre>
              </div>
            )}
          </div>
          <div className="items-center px-4 py-3">
            <button
              id="ok-btn"
              className="px-4 py-2 bg-primary text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-accent focus:outline-none focus:ring-2 focus:ring-primary"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const FreightTable = ({ freights, loading }) => {
  const [selectedFreight, setSelectedFreight] = React.useState(null);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 animate-spin text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M20 4h-5l-1 1" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 9a9 9 0 0114.13-5.13M4 15a9 9 0 0014.13 5.13" />
        </svg>
        <span className="ml-2">Loading data...</span>
      </div>
    );
  }

  if (freights.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No freight offers found. Try applying different filters or refreshing.
      </div>
    );
  }

  const displayedFreights = freights;

  return (
    <>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Loading</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Unloading</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Details</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Add. Desc</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Price Offer</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Dist from Us</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Route</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedFreights.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-all duration-150">
                  {/* 1. Loading + Date */}
                  <td className="px-4 py-3 align-top">
                    <div className="font-medium text-gray-900">{item.loading_place}</div>
                    <div className="text-xs text-gray-500">{item.loading_date || '-'}</div>
                  </td>

                  {/* 2. Unloading + Date */}
                  <td className="px-4 py-3 align-top">
                    <div className="font-medium text-gray-900">{item.unloading_place}</div>
                    <div className="text-xs text-gray-500">{item.unloading_date || '-'}</div>
                  </td>

                  {/* 3. Details: Capacity + LDM + Body Type */}
                  <td className="px-4 py-3 align-top">
                    <div className="space-y-1">
                      {item.capacity && <div className="text-xs">Cap: {item.capacity}</div>}
                      {item.ldm && <div className="text-xs">LDM: {item.ldm}</div>}
                      {item.body_type && <div className="text-xs font-semibold">{item.body_type}</div>}
                      {!item.capacity && !item.ldm && !item.body_type && <span className="text-gray-400">-</span>}
                    </div>
                  </td>

                  {/* 4. Additional Description */}
                  <td className="px-4 py-3 align-top">
                    <div className="text-xs text-gray-600 max-w-xs truncate" title={item.additional_description}>
                      {item.additional_description || '-'}
                    </div>
                  </td>

                  {/* 5. Price Offer + Terms */}
                  <td className="px-4 py-3 align-top">
                    <div className="text-sm font-bold text-green-600">
                      {item.price_original ? `${item.price_original} ${item.currency}` : 'N/A'}
                    </div>
                    {item.payment_terms && <div className="text-xs text-gray-500">{item.payment_terms}</div>}
                  </td>

                  {/* 6. Distance from us */}
                  <td className="px-4 py-3 align-top">
                    <div className="text-gray-900">
                      {item.distance_origin_to_loading ? `${Math.round(item.distance_origin_to_loading)} km` : '-'}
                    </div>
                  </td>

                  {/* 7. Route (Distance A->B) */}
                  <td className="px-4 py-3 align-top">
                    <div className="text-gray-900">
                      {item.distance_km ? `${Math.round(item.distance_km)} km` : '-'}
                    </div>
                  </td>

                  {/* 8. Details Link */}
                  <td className="px-4 py-3 align-top">
                    <button
                      onClick={() => setSelectedFreight(item)}
                      className="text-primary hover:text-accent font-medium text-sm border border-primary px-2 py-1 rounded"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {selectedFreight && <DetailsModal freight={selectedFreight} onClose={() => setSelectedFreight(null)} />}
    </>
  );
};
export default FreightTable;
