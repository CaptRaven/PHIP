import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function RiskMap({ items }) {
  const center = [9.0820, 8.6753]; // Nigeria Center

  return (
    <div className="h-full w-full rounded-lg overflow-hidden border bg-gray-100 relative z-0">
      <MapContainer center={center} zoom={6} scrollWheelZoom={true} className="h-full w-full z-0">
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {items.map((it, idx) => {
          const color = it.risk_category === 'High' ? 'red' : it.risk_category === 'Medium' ? 'orange' : 'green';
          const lat = it.latitude ?? center[0];
          const lon = it.longitude ?? center[1];
          return (
            <CircleMarker 
              key={idx} 
              center={[lat, lon]} 
              radius={12} 
              pathOptions={{ color, fillColor: color, fillOpacity: 0.6 }}
            >
              <Popup>
                <div className="min-w-[200px]">
                  <div className="font-bold text-base mb-1">{it.lga}, {it.state}</div>
                  <div className="text-sm text-gray-600 mb-2">Disease: <span className="font-medium">{it.disease}</span></div>
                  
                  <div className="flex items-center justify-between bg-gray-50 p-2 rounded mb-2">
                    <span className="text-sm">Risk Score:</span>
                    <span className={`font-bold ${
                      it.risk_category === 'High' ? 'text-red-600' : 
                      it.risk_category === 'Medium' ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {it.risk_score.toFixed(2)} ({it.risk_category})
                    </span>
                  </div>

                  {it.top_factors && it.top_factors.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 mb-1">Top Drivers:</div>
                      <ul className="text-xs list-disc pl-4 space-y-1">
                        {it.top_factors.map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white p-3 rounded shadow z-[1000] text-sm">
        <div className="font-semibold mb-2">Risk Levels</div>
        <div className="flex items-center space-x-2 mb-1">
          <span className="w-3 h-3 rounded-full bg-red-500"></span>
          <span>High (0.7 - 1.0)</span>
        </div>
        <div className="flex items-center space-x-2 mb-1">
          <span className="w-3 h-3 rounded-full bg-orange-500"></span>
          <span>Medium (0.3 - 0.7)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-green-500"></span>
          <span>Low (0.0 - 0.3)</span>
        </div>
      </div>
    </div>
  );
}
