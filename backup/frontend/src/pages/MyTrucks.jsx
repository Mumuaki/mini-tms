import React, { useEffect, useState } from 'react';
import { Truck, MapPin, RefreshCw, Save, Plus, Edit2, Trash2 } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const MyTrucks = () => {
    const [trucks, setTrucks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [editingTruck, setEditingTruck] = useState(null);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        truck_type: 'Тентованный фургон',
        cargo_length: '',
        cargo_width: '',
        cargo_height: '',
        license_plate: '',
        driver_name: '',
        gps_vehicle_code: ''
    });

    const fetchTrucks = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`${API_URL}/trucks`);
            setTrucks(response.data);
        } catch (error) {
            console.error('Error fetching trucks:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTrucks();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                cargo_length: formData.cargo_length ? parseFloat(formData.cargo_length) : null,
                cargo_width: formData.cargo_width ? parseFloat(formData.cargo_width) : null,
                cargo_height: formData.cargo_height ? parseFloat(formData.cargo_height) : null,
            };

            if (editingTruck) {
                await axios.patch(`${API_URL}/trucks/${editingTruck.id}`, payload);
            } else {
                await axios.post(`${API_URL}/trucks`, payload);
            }

            setShowForm(false);
            setEditingTruck(null);
            setFormData({
                truck_type: 'Тентованный фургон',
                cargo_length: '',
                cargo_width: '',
                cargo_height: '',
                license_plate: '',
                driver_name: '',
                gps_vehicle_code: ''
            });
            fetchTrucks();
        } catch (error) {
            console.error('Error saving truck:', error);
        }
    };

    const handleEdit = (truck) => {
        setEditingTruck(truck);
        setFormData({
            truck_type: truck.truck_type || 'Тентованный фургон',
            cargo_length: truck.cargo_length || '',
            cargo_width: truck.cargo_width || '',
            cargo_height: truck.cargo_height || '',
            license_plate: truck.license_plate || '',
            driver_name: truck.driver_name || '',
            gps_vehicle_code: truck.gps_vehicle_code || ''
        });
        setShowForm(true);
    };

    const handleDelete = async (truckId) => {
        if (!window.confirm('Are you sure you want to delete this truck?')) return;
        try {
            await axios.delete(`${API_URL}/trucks/${truckId}`);
            fetchTrucks();
        } catch (error) {
            console.error('Error deleting truck:', error);
        }
    };

    const handleUpdateGPS = async (truckId) => {
        try {
            const response = await axios.post(`${API_URL}/trucks/${truckId}/update-gps`);
            if (response.data.success) {
                fetchTrucks();
                alert(`GPS updated: ${response.data.location}`);
            }
        } catch (error) {
            console.error('Error updating GPS:', error);
            alert('Failed to update GPS: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleUseLocation = (location) => {
        // Store in localStorage to be picked up by FreightList
        localStorage.setItem('truck_location', location);
        alert(`Location "${location}" saved! Go to Freights page to use it.`);
    };

    if (loading) {
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
                    <h1 className="text-2xl font-bold text-gray-900">My Trucks</h1>
                    <p className="text-gray-500 mt-1">Manage your fleet and GPS tracking</p>
                </div>
                <button
                    onClick={() => {
                        setShowForm(true);
                        setEditingTruck(null);
                        setFormData({
                            truck_type: 'Тентованный фургон',
                            cargo_length: '',
                            cargo_width: '',
                            cargo_height: '',
                            license_plate: '',
                            driver_name: '',
                            gps_vehicle_code: ''
                        });
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
                >
                    <Plus className="w-4 h-4" />
                    Add Truck
                </button>
            </div>

            {showForm && (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        {editingTruck ? 'Edit Truck' : 'Add New Truck'}
                    </h2>
                    <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Truck Type
                            </label>
                            <input
                                type="text"
                                value={formData.truck_type}
                                onChange={(e) => setFormData({ ...formData, truck_type: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                License Plate
                            </label>
                            <input
                                type="text"
                                value={formData.license_plate}
                                onChange={(e) => setFormData({ ...formData, license_plate: e.target.value })}
                                placeholder="e.g. AB 1234 CD"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Driver Name
                            </label>
                            <input
                                type="text"
                                value={formData.driver_name}
                                onChange={(e) => setFormData({ ...formData, driver_name: e.target.value })}
                                placeholder="Full name"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                GPS Vehicle Code
                            </label>
                            <input
                                type="text"
                                value={formData.gps_vehicle_code}
                                onChange={(e) => setFormData({ ...formData, gps_vehicle_code: e.target.value })}
                                placeholder="From GPS Dozor"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Cargo Length (m)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={formData.cargo_length}
                                onChange={(e) => setFormData({ ...formData, cargo_length: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Cargo Width (m)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={formData.cargo_width}
                                onChange={(e) => setFormData({ ...formData, cargo_width: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Cargo Height (m)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={formData.cargo_height}
                                onChange={(e) => setFormData({ ...formData, cargo_height: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                        </div>

                        <div className="md:col-span-2 flex gap-3 justify-end">
                            <button
                                type="button"
                                onClick={() => {
                                    setShowForm(false);
                                    setEditingTruck(null);
                                }}
                                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
                            >
                                <Save className="w-4 h-4" />
                                Save
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {trucks.map((truck) => (
                    <div key={truck.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <Truck className="w-6 h-6 text-blue-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900">{truck.license_plate || 'No Plate'}</h3>
                                    <p className="text-sm text-gray-500">{truck.truck_type}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleEdit(truck)}
                                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                                >
                                    <Edit2 className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => handleDelete(truck.id)}
                                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-500">Driver:</span>
                                <span className="font-medium text-gray-900">{truck.driver_name || '-'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">GPS Code:</span>
                                <span className="font-medium text-gray-900">{truck.gps_vehicle_code || '-'}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Dimensions:</span>
                                <span className="font-medium text-gray-900">
                                    {truck.cargo_length && truck.cargo_width && truck.cargo_height
                                        ? `${truck.cargo_length}×${truck.cargo_width}×${truck.cargo_height}m`
                                        : '-'}
                                </span>
                            </div>
                        </div>

                        <div className="mt-4 pt-4 border-t border-gray-200">
                            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                <MapPin className="w-4 h-4" />
                                <span className="font-medium">GPS Location</span>
                            </div>
                            {truck.last_known_location ? (
                                <div className="space-y-2">
                                    <p className="text-sm font-medium text-gray-900">{truck.last_known_location}</p>
                                    <p className="text-xs text-gray-500">
                                        Updated: {truck.gps_updated_at ? new Date(truck.gps_updated_at).toLocaleString() : 'Never'}
                                    </p>
                                    <button
                                        onClick={() => handleUseLocation(truck.last_known_location)}
                                        className="w-full text-xs px-3 py-1.5 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 font-medium transition-colors"
                                    >
                                        Use for Search
                                    </button>
                                </div>
                            ) : (
                                <p className="text-sm text-gray-400">No location data</p>
                            )}
                        </div>

                        <button
                            onClick={() => truck.gps_vehicle_code ? handleUpdateGPS(truck.id) : alert('Please add GPS Vehicle Code first (click Edit button)')}
                            disabled={!truck.gps_vehicle_code}
                            className={`mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg font-medium transition-colors text-sm ${truck.gps_vehicle_code
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                }`}
                            title={truck.gps_vehicle_code ? 'Update GPS location' : 'GPS Vehicle Code not set'}
                        >
                            <RefreshCw className="w-4 h-4" />
                            {truck.gps_vehicle_code ? 'Update GPS' : 'GPS Code Required'}
                        </button>
                    </div>
                ))}

                {trucks.length === 0 && (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        No trucks found. Click "Add Truck" to get started.
                    </div>
                )}
            </div>
        </div>
    );
};

export default MyTrucks;
