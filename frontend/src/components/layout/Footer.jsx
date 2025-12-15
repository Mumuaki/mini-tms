import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t mt-8 py-6">
      <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
        <p>TMSmini Gemini &copy; {currentYear}. This tool is for demonstration purposes only.</p>
        <p className="mt-1">
          Data is sourced from various platforms.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
