import { useState, useEffect } from 'react';
import axios from 'axios';
import AlertCard from '../components/AlertCard';
import { API_BASE } from '../config';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_BASE}/predictions/alerts`)
      .then(res => {
        setAlerts(res.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Active Alerts</h2>
        <div className="flex space-x-2">
          <button className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm font-medium">High Priority</button>
          <button className="px-3 py-1 bg-gray-100 text-gray-600 rounded text-sm">All Alerts</button>
        </div>
      </div>

      {loading ? (
        <div>Loading alerts...</div>
      ) : (
        <div className="grid gap-4">
          {alerts.length === 0 ? (
            <div className="text-gray-500">No active alerts at this time.</div>
          ) : (
            alerts.map((alert, idx) => (
              <AlertCard key={idx} alert={alert} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
