import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import DashboardPage from './pages/DashboardPage';
import TrucksPage from './pages/TrucksPage';

function App() {
  return (
    <Router>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/trucks" element={<TrucksPage />} />
          {/* Other routes can be added here later */}
        </Routes>
      </DashboardLayout>
    </Router>
  );
}

export default App;

