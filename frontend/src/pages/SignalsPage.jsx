import SignalCard from '../components/SignalCard';

// Mock data generator
const genTrend = () => Array.from({ length: 10 }, () => ({ val: Math.random() * 100 }));

export default function SignalsPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Community & Environmental Signals</h2>
        <div className="text-sm text-gray-500">Real-time monitoring from sentinel sites</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SignalCard 
          title="Weekly Fever Reports" 
          value="1,240" 
          change={12} 
          trendData={genTrend()} 
          color="#ef4444" 
        />
        <SignalCard 
          title="Diarrhea Cases" 
          value="342" 
          change={-5} 
          trendData={genTrend()} 
          color="#f59e0b" 
        />
        <SignalCard 
          title="Rainfall (mm)" 
          value="85mm" 
          change={45} 
          trendData={genTrend()} 
          color="#3b82f6" 
        />
        <SignalCard 
          title="Pharmacy Antibiotics Sales" 
          value="4,500" 
          change={8} 
          trendData={genTrend()} 
          color="#8b5cf6" 
        />
        <SignalCard 
          title="School Absenteeism" 
          value="15%" 
          change={2} 
          trendData={genTrend()} 
          color="#64748b" 
        />
        <SignalCard 
          title="Flood Risk Index" 
          value="0.65" 
          change={0} 
          trendData={genTrend()} 
          color="#06b6d4" 
        />
      </div>
    </div>
  );
}
