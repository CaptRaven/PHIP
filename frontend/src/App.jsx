import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import MapPage from './pages/MapPage';
import TrendsPage from './pages/TrendsPage';
import SignalsPage from './pages/SignalsPage';
import AlertsPage from './pages/AlertsPage';
import FacilityLogin from './pages/FacilityLogin';
import FacilityRegister from './pages/FacilityRegister';
import FacilityDashboard from './pages/FacilityDashboard';

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Facility Portal Routes (No Sidebar) */}
        <Route path="/facility/login" element={<FacilityLogin />} />
        <Route path="/facility/register" element={<FacilityRegister />} />
        <Route path="/facility/dashboard" element={<FacilityDashboard />} />

        {/* Main Dashboard Routes (With Sidebar) */}
        <Route path="/*" element={
          <Layout>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/map" element={<MapPage />} />
              <Route path="/trends" element={<TrendsPage />} />
              <Route path="/signals" element={<SignalsPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        } />
      </Routes>
    </Router>
  );
}
