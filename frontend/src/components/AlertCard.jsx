import { AlertTriangle } from 'lucide-react';

export default function AlertCard({ alert }) {
  const isHigh = alert.level === 'High';
  const colorClass = isHigh ? 'border-l-red-500' : 'border-l-yellow-500';
  const bgClass = isHigh ? 'bg-red-50' : 'bg-yellow-50';
  const textClass = isHigh ? 'text-red-700' : 'text-yellow-700';

  return (
    <div className={`bg-white border rounded-r-lg border-l-4 p-4 shadow-sm ${colorClass}`}>
      <div className="flex justify-between items-start">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-full ${bgClass}`}>
            <AlertTriangle className={textClass} size={24} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-bold text-lg">{alert.level.toUpperCase()} RISK ALERT</h3>
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-600">
                Score: {alert.risk_score.toFixed(2)}
              </span>
            </div>
            <div className="text-gray-600 font-medium mt-1">
              {alert.location?.lga}, {alert.location?.state}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              Disease: <span className="font-semibold">{alert.disease}</span> • Forecast: Next 2-4 weeks
            </div>
            
            <div className="mt-3">
              <div className="text-xs font-semibold text-gray-500 uppercase">Main Drivers</div>
              <ul className="list-disc list-inside text-sm text-gray-700 mt-1">
                {/* Mock drivers if not present, real API will have them later */}
                <li>High rainfall spike observed</li>
                <li>Rising fever reports in community</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="text-xs text-gray-400">
          {new Date(alert.created_at_week).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}
