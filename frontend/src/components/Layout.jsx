import React from 'react';
import { Link, useLocation } from 'react-router-dom';
<<<<<<< HEAD

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

=======
import { Truck, LayoutDashboard, Settings, Search } from 'lucide-react';
import clsx from 'clsx';

const NavItem = ({ to, icon: Icon, children }) => {
    const location = useLocation();
    const isActive = location.pathname === to;

    return (
        <Link
            to={to}
            className={clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm font-medium',
                isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
            )}
        >
            <Icon className="w-5 h-5" />
            {children}
        </Link>
    );
};

const Layout = ({ children }) => {
    return (
        <div className="min-h-screen bg-gray-50 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-gray-200 fixed h-full z-10">
                <div className="h-16 flex items-center px-6 border-b border-gray-200">
                    <Truck className="w-8 h-8 text-blue-600 mr-2" />
                    <span className="text-xl font-bold text-gray-900">Mini-TMS</span>
                </div>

                <nav className="p-4 space-y-1">
                    <NavItem to="/trucks" icon={Truck}>My Trucks</NavItem>
                    <NavItem to="/freights" icon={Search}>Freights</NavItem>
                    <NavItem to="/settings" icon={Settings}>Settings</NavItem>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 ml-64 p-8">
                <div className="max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
>>>>>>> 97953c3 (Initial commit from Specify template)
