import { useState, useEffect } from 'react';
import axios from 'axios';
import RiskMap from '../components/RiskMap';

const API_BASE = 'http://localhost:8000';

export default function MapPage() {
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [disease, setDisease] = useState('cholera');

  useEffect(() => {
    setLoading(true);
    axios.get(`${API_BASE}/predictions/heatmap-data?disease=${disease}`)
      .then(res => {
        setHeatmap(res.data.items || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [disease]);

  return (
    <div className="flex flex-col h-[calc(100vh-100px)]">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Geographic Risk Distribution</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Disease Layer:</span>
          <select 
            value={disease} 
            onChange={e => setDisease(e.target.value)} 
            className="border rounded px-3 py-1 bg-white"
          >
            <option value="cholera">Cholera</option>
            <option value="malaria">Malaria</option>
            <option value="lassa">Lassa Fever</option>
            <option value="meningitis">Meningitis</option>
          </select>
        </div>
      </div>
      
      <div className="flex-1 bg-white rounded-lg border shadow-sm p-1">
        {loading ? (
          <div className="h-full flex items-center justify-center">Loading map data...</div>
        ) : (
          <RiskMap items={heatmap} />
        )}
      </div>
    </div>
  );
}
