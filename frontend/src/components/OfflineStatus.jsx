import { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { offlineStorage } from '../utils/offlineStorage';

const API_BASE = 'http://localhost:8000';

export default function OfflineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      syncReports();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial check for pending items
    checkPending();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const checkPending = async () => {
    const reports = await offlineStorage.getPendingReports();
    setPendingCount(reports.length);
  };

  const syncReports = async () => {
    const reports = await offlineStorage.getPendingReports();
    if (reports.length === 0) return;

    setSyncing(true);
    const token = localStorage.getItem('token');
    
    // Process sequentially
    for (const report of reports) {
      try {
        // Remove offline-specific fields before sending
        const { id, createdAt, status, ...payload } = report;
        
        await axios.post(`${API_BASE}/reports/`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Remove from offline store if successful
        await offlineStorage.deleteReport(id);
      } catch (err) {
        console.error("Sync failed for report:", report, err);
        // Keep in store to retry later
      }
    }
    
    await checkPending();
    setSyncing(false);
  };

  if (isOnline && pendingCount === 0) return null;

  return (
    <div className={`w-full px-4 py-2 flex justify-between items-center text-sm font-medium ${
      isOnline ? 'bg-blue-600 text-white' : 'bg-red-600 text-white'
    }`}>
      <div className="flex items-center">
        {isOnline ? <Wifi size={16} className="mr-2" /> : <WifiOff size={16} className="mr-2" />}
        {isOnline ? 'Online Mode' : 'Offline Mode'}
      </div>
      
      {pendingCount > 0 && (
        <div className="flex items-center space-x-3">
          <span>{pendingCount} pending reports</span>
          {isOnline && (
            <button 
              onClick={syncReports} 
              disabled={syncing}
              className="flex items-center bg-white/20 hover:bg-white/30 px-2 py-1 rounded transition-colors"
            >
              <RefreshCw size={14} className={`mr-1 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
