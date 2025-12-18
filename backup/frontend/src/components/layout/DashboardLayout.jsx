import React from 'react';
import Header from './Header';
import Footer from './Footer';

const DashboardLayout = ({ children }) => {
  return (
    <div className="bg-gray-50 min-h-screen flex flex-col font-sans">
      <Header />
      <main className="container mx-auto px-4 py-8 flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default DashboardLayout;
