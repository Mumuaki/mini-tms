import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }) {
  const location = useLocation();

  const navItems = [
    { path: '/trucks', label: '🚚 My Trucks', icon: '▶️' },
    { path: '/freights', label: '📦 Freights', icon: '▶️' },
    { path: '/gps', label: '📍 GPS Tracking', icon: '▶️' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-blue-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">🚚</div>
            <div>
              <h1 className="text-2xl font-bold">Mini-TMS</h1>
              <p className="text-sm opacity-90">Transportation Management System</p>
            </div>
          </div>
          <div className="text-sm opacity-75">v1.0.0</div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-blue-500 text-white">
        <div className="container mx-auto px-4 flex gap-6">
          {navItems.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-4 py-3 border-b-4 transition ${
                location.pathname === item.path
                  ? 'border-yellow-300 font-bold'
                  : 'border-transparent hover:border-blue-300'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white text-center py-4 mt-12">
        <p>© 2025 Mini-TMS. All rights reserved.</p>
      </footer>
    </div>
  );
}

