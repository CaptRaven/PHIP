import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Map, TrendingUp, Radio, AlertTriangle } from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Overview', path: '/', icon: LayoutDashboard },
  { label: 'Risk Map', path: '/map', icon: Map },
  { label: 'Trends', path: '/trends', icon: TrendingUp },
  { label: 'Signals Monitor', path: '/signals', icon: Radio },
  { label: 'Alerts', path: '/alerts', icon: AlertTriangle },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-white border-r h-screen fixed left-0 top-0 flex flex-col z-10">
      <div className="p-4 border-b flex items-center">
        <div className="font-bold text-xl text-blue-900">PHIP Nigeria</div>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t text-xs text-gray-400">
        v1.0.0 Beta
      </div>
    </aside>
  );
}
