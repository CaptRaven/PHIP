import { useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';

// Mock data for trends (since real historical API is not fully built for charts yet)
const MOCK_TRENDS = Array.from({ length: 24 }, (_, i) => ({
  week: `W${i + 1}`,
  cases: Math.floor(Math.random() * 100),
  risk: 0.3 + Math.random() * 0.6,
  rainfall: Math.floor(Math.random() * 200),
  sales: 1000 + Math.floor(Math.random() * 500)
}));

export default function TrendsPage() {
  const [filters, setFilters] = useState({ state: 'Kano', lga: 'Kano Municipal', disease: 'Cholera' });

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border shadow-sm flex flex-wrap gap-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">State</label>
          <select className="border rounded px-3 py-1 w-40">
            <option>Kano</option>
            <option>Lagos</option>
            <option>Kaduna</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">LGA</label>
          <select className="border rounded px-3 py-1 w-40">
            <option>Kano Municipal</option>
            <option>Gwale</option>
            <option>Dala</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Disease</label>
          <select className="border rounded px-3 py-1 w-40">
            <option>Cholera</option>
            <option>Malaria</option>
          </select>
        </div>
      </div>

      {/* Main Chart: Risk vs Cases */}
      <div className="bg-white p-4 rounded-lg border shadow-sm">
        <h3 className="font-semibold mb-4">Disease Cases vs Predicted Risk Score</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={MOCK_TRENDS}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="week" />
              <YAxis yAxisId="left" label={{ value: 'Cases', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 1]} label={{ value: 'Risk Score', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="cases" stroke="#ef4444" strokeWidth={2} dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="risk" stroke="#3b82f6" strokeWidth={2} dot={false} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rainfall */}
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <h3 className="font-semibold mb-4">Rainfall (mm) vs Cases</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={MOCK_TRENDS}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="rainfall" fill="#60a5fa" name="Rainfall" />
                <Line type="monotone" dataKey="cases" stroke="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pharmacy Sales */}
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <h3 className="font-semibold mb-4">Pharmacy Sales Index</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={MOCK_TRENDS}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="sales" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
