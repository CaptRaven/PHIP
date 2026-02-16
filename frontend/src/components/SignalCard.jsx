import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

export default function SignalCard({ title, value, change, trendData, color = "#3b82f6" }) {
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <div className="text-gray-500 text-sm">{title}</div>
        <div className={`text-xs px-2 py-0.5 rounded-full flex items-center ${
          change > 0 ? 'bg-red-50 text-red-700' : change < 0 ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'
        }`}>
          {change > 0 ? <ArrowUp size={10} className="mr-1" /> : change < 0 ? <ArrowDown size={10} className="mr-1" /> : <Minus size={10} className="mr-1" />}
          {Math.abs(change)}%
        </div>
      </div>
      <div className="text-2xl font-bold mb-4">{value}</div>
      <div className="h-16">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <Line type="monotone" dataKey="val" stroke={color} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
