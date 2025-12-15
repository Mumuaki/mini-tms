import React, { useState, useEffect } from 'react';

const TruckFormModal = ({ isOpen, onClose, onSave, initialData }) => {
  const initialState = {
    truck_type: 'Тентованный фургон',
    cargo_length: '',
    cargo_width: '',
    cargo_height: '',
    license_plate: '',
    driver_name: '',
    gps_vehicle_code: '',
    is_active: true, // Assuming active by default for new trucks
  };

  const [truck, setTruck] = useState(initialData || initialState);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setTruck(initialData || initialState);
  }, [initialData, isOpen]); // Reset form when modal opens or initialData changes

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTruck(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    
    const payload = { ...truck };
    // Convert empty strings to null for optional numeric fields
    ['cargo_length', 'cargo_width', 'cargo_height'].forEach(field => {
      if (payload[field] === '') {
        payload[field] = null;
      } else {
        payload[field] = parseFloat(payload[field]); // Ensure it's a number
      }
    });

    await onSave(payload);
    setIsSaving(false);
  };

  if (!isOpen) return null;

  const title = initialData ? "Edit Truck" : "Add New Truck";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 gap-4">
            <label className="block">
              <span className="text-gray-700">License Plate</span>
              <input type="text" name="license_plate" placeholder="e.g. AB-123-CD" value={truck.license_plate || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
            </label>
            <label className="block">
              <span className="text-gray-700">Driver Name</span>
              <input type="text" name="driver_name" placeholder="Driver Name" value={truck.driver_name || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
            </label>
            <label className="block">
              <span className="text-gray-700">Truck Type</span>
              <input type="text" name="truck_type" placeholder="e.g. Тентованный фургон" value={truck.truck_type || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
            </label>
            
            <div className="grid grid-cols-3 gap-2">
              <label className="block">
                <span className="text-gray-700">Length (m)</span>
                <input type="number" step="0.01" name="cargo_length" placeholder="Length" value={truck.cargo_length || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
              </label>
              <label className="block">
                <span className="text-gray-700">Width (m)</span>
                <input type="number" step="0.01" name="cargo_width" placeholder="Width" value={truck.cargo_width || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
              </label>
              <label className="block">
                <span className="text-gray-700">Height (m)</span>
                <input type="number" step="0.01" name="cargo_height" placeholder="Height" value={truck.cargo_height || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
              </label>
            </div>

            <label className="block">
              <span className="text-gray-700">GPS Dozor Vehicle Code</span>
              <input type="text" name="gps_vehicle_code" placeholder="Vehicle Code" value={truck.gps_vehicle_code || ''} onChange={handleChange} className="mt-1 block w-full p-2 border border-gray-300 rounded-md" />
            </label>
            
            {initialData && ( // Only show active status for existing trucks
              <label className="inline-flex items-center mt-3">
                <input type="checkbox" name="is_active" checked={truck.is_active} onChange={handleChange} className="form-checkbox h-5 w-5 text-primary rounded" />
                <span className="ml-2 text-gray-700">Is Active</span>
              </label>
            )}
          </div>
          <div className="flex justify-end space-x-4 mt-6">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-200 rounded">Cancel</button>
            <button type="submit" disabled={isSaving} className="px-4 py-2 bg-primary text-white rounded disabled:opacity-50">
              {isSaving ? 'Saving...' : 'Save Truck'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TruckFormModal;
