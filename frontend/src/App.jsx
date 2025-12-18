import React from 'react';
<<<<<<< HEAD
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import MyTrucks from './pages/MyTrucks';
import FreightList from './pages/FreightList';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trucks" element={<MyTrucks />} />
          <Route path="/freights" element={<FreightList />} />
        </Routes>
      </Layout>
    </BrowserRouter>
=======
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
>>>>>>> 97953c3 (Initial commit from Specify template)
  );
}

export default App;

