import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { truckService } from '../services/api';
import TruckFormModal from '../components/trucks/TruckFormModal';

const TrucksPage = () => {
  const navigate = useNavigate();
  const [trucks, setTrucks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTruck, setEditingTruck] = useState(null); // State to hold truck being edited

  const fetchTrucks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await truckService.getAll();
      setTrucks(data);
    } catch (err) {
      setError('Failed to load trucks.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrucks();
  }, [fetchTrucks]);

  const handleOpenAddModal = () => {
    setEditingTruck(null); // Clear any editing state
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (truck) => {
    setEditingTruck(truck);
    setIsModalOpen(true);
  };

  const handleSaveTruck = async (truckData) => {
    try {
      if (editingTruck) {
        // Update existing truck
        await truckService.update(editingTruck.id, truckData);
      } else {
        // Create new truck
        await truckService.create(truckData);
      }
      setIsModalOpen(false);
      setEditingTruck(null); // Clear editing state
      fetchTrucks(); // Refresh the list
    } catch (err) {
      alert('Failed to save truck. Check console for details.');
      console.error(err);
    }
  };

  const handleDeleteTruck = async (truckId) => {
    if (window.confirm('Are you sure you want to delete this truck?')) {
      try {
        await truckService.delete(truckId);
        fetchTrucks(); // Refresh the list
      } catch (err) {
        alert('Failed to delete truck. Check console for details.');
        console.error(err);
      }
    }
  };

  const handleUpdateGps = async (truckId) => {
    try {
      await truckService.updateGps(truckId);
      fetchTrucks(); // Refresh the list to show new location
    } catch (err) {
      alert(`Failed to update GPS for truck ${truckId}. Check console for details.`);
      console.error(err);
    }
  };

  const handleFindLoadsFromHere = (truck) => {
    if (truck.last_known_location) {
      navigate('/', { state: { originFilter: truck.last_known_location } });
    } else if (truck.gps_vehicle_code) {
      // If we have GPS code but no saved location, pass ID so Dashboard can fetch it
      navigate('/', { state: { truckId: truck.id } });
    } else {
      alert('Please update GPS location or add GPS Vehicle Code first.');
    }
  };

  return (
    <div className="space-y-6">
      <TruckFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveTruck}
        initialData={editingTruck}
      />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Trucks</h1>
          <p className="text-gray-500 mt-1">Manage your fleet and view their current status.</p>
        </div>
        <div>
          <button
            onClick={handleOpenAddModal}
            className="bg-primary hover:bg-accent text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Add New Truck
          </button>
        </div>
      </div>

      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">License Plate</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Truck Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Driver</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Known Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">GPS Updated</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan="6" className="text-center py-8">Loading...</td></tr>
              ) : trucks.map(truck => (
                <tr key={truck.id}>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{truck.license_plate || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{truck.truck_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{truck.driver_name || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{truck.last_known_location || 'Unknown'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {truck.gps_updated_at ? new Date(truck.gps_updated_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 flex items-center space-x-2">
                    <button
                      onClick={() => handleUpdateGps(truck.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Update GPS
                    </button>
                    <button
                      onClick={() => handleOpenEditModal(truck)}
                      className="text-orange-600 hover:text-orange-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTruck(truck.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                    <button
                      onClick={() => handleFindLoadsFromHere(truck)}
                      className="text-green-600 hover:text-green-900"
                    >
                      Find Loads
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && trucks.length === 0 && (
                <tr><td colSpan="6" className="text-center py-8 text-gray-500">No trucks found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TrucksPage;