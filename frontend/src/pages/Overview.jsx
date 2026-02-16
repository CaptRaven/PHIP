import { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE = 'http://localhost:8000';

function StatCard({ label, count, color, trend }) {
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <div className="text-gray-500 text-sm mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{count}</div>
      {trend && (
        <div className="flex items-center text-xs mt-2 text-gray-400">
          {trend > 0 ? <ArrowUp size={12} className="text-red-500 mr-1" /> : <ArrowDown size={12} className="text-green-500 mr-1" />}
          <span>{Math.abs(trend)}% from last week</span>
        </div>
      )}
    </div>
  );
}

export default function Overview() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ high: 0, medium: 0, low: 0 });
  const [topRisks, setTopRisks] = useState([]);

  useEffect(() => {
    // Fetch heatmap data to aggregate stats
    axios.get(`${API_BASE}/predictions/heatmap-data?disease=cholera`)
      .then(res => {
        const items = res.data.items || [];
        const high = items.filter(i => i.risk_category === 'High').length;
        const medium = items.filter(i => i.risk_category === 'Medium').length;
        const low = items.filter(i => i.risk_category === 'Low').length;
        
        setStats({ high, medium, low });
        
        // Top 5 risky locations
        const sorted = [...items].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);
        setTopRisks(sorted);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // Mock trend data
  const trendData = Array.from({ length: 12 }, (_, i) => ({
    week: `W${i + 1}`,
    risk: 0.2 + Math.random() * 0.3,
    cases: Math.floor(Math.random() * 50)
  }));

  if (loading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="High Risk LGAs" count={stats.high} color="text-red-600" trend={12} />
        <StatCard label="Medium Risk LGAs" count={stats.medium} color="text-yellow-600" trend={-5} />
        <StatCard label="Low Risk LGAs" count={stats.low} color="text-green-600" trend={2} />
        <div className="bg-white p-4 rounded-lg border shadow-sm flex items-center justify-between">
          <div>
            <div className="text-gray-500 text-sm">Monitored Disease</div>
            <div className="font-semibold">Cholera</div>
          </div>
          <select className="border rounded text-sm p-1">
            <option>Cholera</option>
            <option>Malaria</option>
            <option>Lassa</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-4 rounded-lg border shadow-sm">
          <h3 className="font-semibold mb-4">National Risk Trend (12 Weeks)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis dataKey="week" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line yAxisId="left" type="monotone" dataKey="risk" stroke="#2563eb" name="Avg Risk Score" />
                <Line yAxisId="right" type="monotone" dataKey="cases" stroke="#dc2626" name="Reported Cases" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <h3 className="font-semibold mb-4">Top Risk Locations</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-gray-500 border-b">
                <tr>
                  <th className="pb-2">LGA</th>
                  <th className="pb-2">State</th>
                  <th className="pb-2">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {topRisks.map((item, idx) => (
                  <tr key={idx}>
                    <td className="py-2 font-medium">{item.lga}</td>
                    <td className="py-2 text-gray-500">{item.state}</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        item.risk_category === 'High' ? 'bg-red-100 text-red-800' :
                        item.risk_category === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {item.risk_score.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
