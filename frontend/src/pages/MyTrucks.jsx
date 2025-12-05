import React, { useState } from 'react';
import { useTrucks } from '../hooks/useTrucks';

export default function MyTrucks() {
  const { trucks, loading, error, addTruck, updateTruck, deleteTruck, updateGPS } = useTrucks();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    truckType: '',
    cargoLength: 13.5,
    cargoWidth: 2.5,
    cargoHeight: 2.7,
    licensePlate: '',
    driverName: '',
    gpsVehicleCode: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await addTruck(formData);
      setFormData({
        truckType: '',
        cargoLength: 13.5,
        cargoWidth: 2.5,
        cargoHeight: 2.7,
        licensePlate: '',
        driverName: '',
        gpsVehicleCode: '',
      });
      setShowForm(false);
    } catch (err) {
      console.error('Failed to add truck:', err);
    }
  };

  if (loading) return <div className="text-center py-8">Loading trucks...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold">🚚 My Trucks</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          {showForm ? '✕ Cancel' : '➕ Add Truck'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded shadow mb-6">
          <h3 className="text-xl font-bold mb-4">Register New Truck</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Truck Type"
                value={formData.truckType}
                onChange={(e) => setFormData({ ...formData, truckType: e.target.value })}
                required
                className="border px-3 py-2 rounded"
              />
              <input
                type="text"
                placeholder="License Plate"
                value={formData.licensePlate}
                onChange={(e) => setFormData({ ...formData, licensePlate: e.target.value })}
                required
                className="border px-3 py-2 rounded"
              />
              <input
                type="text"
                placeholder="Driver Name"
                value={formData.driverName}
                onChange={(e) => setFormData({ ...formData, driverName: e.target.value })}
                required
                className="border px-3 py-2 rounded"
              />
              <input
                type="text"
                placeholder="GPS Vehicle Code (e.g., ODOKIRAGEN)"
                value={formData.gpsVehicleCode}
                onChange={(e) => setFormData({ ...formData, gpsVehicleCode: e.target.value })}
                required
                className="border px-3 py-2 rounded"
              />
            </div>
            <div className="grid grid-cols-4 gap-4">
              <input
                type="number"
                placeholder="Length (m)"
                value={formData.cargoLength}
                onChange={(e) => setFormData({ ...formData, cargoLength: parseFloat(e.target.value) })}
                className="border px-3 py-2 rounded"
              />
              <input
                type="number"
                placeholder="Width (m)"
                value={formData.cargoWidth}
                onChange={(e) => setFormData({ ...formData, cargoWidth: parseFloat(e.target.value) })}
                className="border px-3 py-2 rounded"
              />
              <input
                type="number"
                placeholder="Height (m)"
                value={formData.cargoHeight}
                onChange={(e) => setFormData({ ...formData, cargoHeight: parseFloat(e.target.value) })}
                className="border px-3 py-2 rounded"
              />
              <button type="submit" className="bg-blue-500 text-white rounded hover:bg-blue-600">
                Save Truck
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {trucks.map(truck => (
          <div key={truck.id} className="bg-white p-4 rounded shadow hover:shadow-lg transition">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-bold text-lg">{truck.licensePlate}</h3>
                <p className="text-sm text-gray-600">Type: {truck.truckType}</p>
                <p className="text-sm text-gray-600">Driver: {truck.driverName}</p>
                <p className="text-sm text-gray-600">
                  Dimensions: {truck.cargoLength}L × {truck.cargoWidth}W × {truck.cargoHeight}H m
                </p>
                {truck.lastKnownLocation && (
                  <p className="text-sm text-green-600 font-semibold">
                    📍 {truck.lastKnownLocation}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => updateGPS(truck.id)}
                  className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                >
                  🔄 Update GPS
                </button>
                <button
                  onClick={() => deleteTruck(truck.id)}
                  className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {trucks.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded">
          <p className="text-gray-600">No trucks registered yet</p>
        </div>
      )}
    </div>
  );
}

