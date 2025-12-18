import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-primary text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🚚</span> 
              <h1 className="text-2xl font-bold">TMSmini Gemini</h1>
            </div>
            <nav className="flex items-center space-x-4">
              <Link to="/" className="text-gray-200 hover:text-white transition-colors">Dashboard</Link>
              <Link to="/trucks" className="text-gray-200 hover:text-white transition-colors">My Trucks</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="display: inline-block w-2 h-2 mr-2 bg-success rounded-full"></span>
              <span>Live</span>
            </div>
            <button 
              id="refreshBtn" 
              className="bg-white text-primary-dark hover:bg-gray-100 font-semibold py-2 px-4 rounded-lg flex items-center transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M20 4h-5l-1 1" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 9a9 9 0 0114.13-5.13M4 15a9 9 0 0014.13 5.13" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
