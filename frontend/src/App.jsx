import React from 'react';
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
  );
}

export default App;

