import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  LogOut, ClipboardList, Activity, AlertTriangle, 
  Thermometer, TrendingUp, TrendingDown, Minus 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import OfflineStatus from '../components/OfflineStatus';
import { offlineStorage } from '../utils/offlineStorage';

const API_BASE = 'http://localhost:8000';

export default function FacilityDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('report');
  const [facility, setFacility] = useState(null);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  
  // Form State
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [formData, setFormData] = useState({
    fever_cases: 0,
    diarrhea_cases: 0,
    vomiting_cases: 0,
    respiratory_cases: 0,
    hospital_admissions: 0,
    severe_dehydration_cases: 0,
    unexplained_deaths: 0,
    bed_occupancy_rate: 0,
    ors_stock_level: 'Normal',
    antibiotics_stock_level: 'Normal',
    notes: ''
  });
  const [submitStatus, setSubmitStatus] = useState({ type: '', msg: '' });

  useEffect(() => {
    const token = localStorage.getItem('token');
    const facData = localStorage.getItem('facility');
    
    if (!token || !facData) {
      navigate('/facility/login');
      return;
    }
    
    setFacility(JSON.parse(facData));
    fetchFeedback(token);
  }, [navigate]);

  const fetchFeedback = async (token) => {
    try {
      const res = await axios.get(`${API_BASE}/reports/feedback`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFeedback(res.data);
    } catch (err) {
      console.error("Error fetching feedback:", err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('facility');
    navigate('/facility/login');
  };

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? 0 : parseInt(value)) : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSubmitStatus({ type: '', msg: '' });

    try {
      const token = localStorage.getItem('token');
      const payload = {
        report_date: reportDate,
        ...formData,
        bed_occupancy_rate: parseFloat(formData.bed_occupancy_rate)
      };

      if (navigator.onLine) {
        await axios.post(`${API_BASE}/reports/`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSubmitStatus({ type: 'success', msg: 'Report submitted successfully!' });
        fetchFeedback(token); 
        setActiveTab('feedback');
      } else {
        await offlineStorage.saveReport(payload);
        setSubmitStatus({ type: 'success', msg: 'Report saved offline. Will sync when online.' });
        // Clear form or keep it?
      }
    } catch (err) {
      console.error(err);
      if (!navigator.onLine) {
         // Fallback if axios fails due to network during execution
         try {
            const payload = {
                report_date: reportDate,
                ...formData,
                bed_occupancy_rate: parseFloat(formData.bed_occupancy_rate)
            };
            await offlineStorage.saveReport(payload);
            setSubmitStatus({ type: 'success', msg: 'Network lost. Report saved offline.' });
         } catch (e) {
             setSubmitStatus({ type: 'error', msg: 'Failed to save offline.' });
         }
      } else {
        setSubmitStatus({ type: 'error', msg: 'Failed to submit report.' });
      }
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data from feedback
  const chartData = feedback ? [
    { name: 'Fever', my: feedback.comparison.my_fever || 0, lga: feedback.comparison.lga_avg_fever || 0 },
    { name: 'Diarrhea', my: feedback.comparison.my_diarrhea || 0, lga: feedback.comparison.lga_avg_diarrhea || 0 },
    { name: 'Respiratory', my: feedback.comparison.my_respiratory || 0, lga: feedback.comparison.lga_avg_respiratory || 0 },
  ] : [];

  if (!facility) return null;

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <OfflineStatus />
      {/* Top Bar */}
      <div className="bg-white shadow-sm border-b px-6 py-4 flex justify-between items-center sticky top-0 z-10">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <ClipboardList className="text-blue-600" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">{facility.name}</h1>
            <p className="text-sm text-gray-500">{facility.type} • {facility.lga}, {facility.state}</p>
          </div>
        </div>
        <button 
          onClick={handleLogout}
          className="flex items-center text-gray-600 hover:text-red-600 transition-colors"
        >
          <LogOut size={18} className="mr-2" />
          Logout
        </button>
      </div>

      <div className="flex-1 container mx-auto p-6 max-w-5xl">
        {/* Tabs */}
        <div className="flex space-x-4 mb-6">
          <button
            onClick={() => setActiveTab('report')}
            className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'report' 
                ? 'bg-blue-600 text-white shadow-md' 
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <ClipboardList size={18} className="mr-2" />
            Daily Report
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'feedback' 
                ? 'bg-purple-600 text-white shadow-md' 
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Activity size={18} className="mr-2" />
            Local Risk & Feedback
          </button>
        </div>

        {/* Report Form */}
        {activeTab === 'report' && (
          <div className="bg-white rounded-xl shadow-sm border p-6 animate-fade-in">
            <div className="mb-6 flex justify-between items-center border-b pb-4">
              <h2 className="text-lg font-semibold text-gray-800">Submit Daily Report</h2>
              <input 
                type="date" 
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                className="border rounded px-3 py-1 text-gray-600"
              />
            </div>

            {submitStatus.msg && (
              <div className={`mb-6 p-4 rounded-lg flex items-center ${
                submitStatus.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
              }`}>
                {submitStatus.type === 'success' ? <ClipboardList className="mr-2" /> : <AlertTriangle className="mr-2" />}
                {submitStatus.msg}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {/* Section A: Symptoms */}
              <div className="mb-8">
                <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Patient Symptom Counts (Today)</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  {['fever', 'diarrhea', 'vomiting', 'respiratory'].map((sym) => (
                    <div key={sym} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                      <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">{sym} Cases</label>
                      <input
                        type="number"
                        min="0"
                        name={`${sym}_cases`}
                        value={formData[`${sym}_cases`]}
                        onChange={handleInputChange}
                        className="w-full text-2xl font-bold bg-white border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Section B: Severe Cases */}
              <div className="mb-8">
                <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Severe Cases & Resources</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Admissions</label>
                    <input
                      type="number"
                      min="0"
                      name="hospital_admissions"
                      value={formData.hospital_admissions}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Severe Dehydration</label>
                    <input
                      type="number"
                      min="0"
                      name="severe_dehydration_cases"
                      value={formData.severe_dehydration_cases}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Deaths (Unexplained)</label>
                    <input
                      type="number"
                      min="0"
                      name="unexplained_deaths"
                      value={formData.unexplained_deaths}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                </div>
              </div>

              {/* Section C: Stocks */}
              <div className="mb-8">
                <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4">Stock Levels</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Bed Occupancy (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      name="bed_occupancy_rate"
                      value={formData.bed_occupancy_rate}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ORS Stock</label>
                    <select
                      name="ors_stock_level"
                      value={formData.ors_stock_level}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      <option>Normal</option>
                      <option>Low</option>
                      <option>Out</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Antibiotics Stock</label>
                    <select
                      name="antibiotics_stock_level"
                      value={formData.antibiotics_stock_level}
                      onChange={handleInputChange}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      <option>Normal</option>
                      <option>Low</option>
                      <option>Out</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Section D: Notes */}
              <div className="mb-8">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                <textarea
                  name="notes"
                  rows="3"
                  placeholder="Any unusual patterns observed?"
                  value={formData.notes}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded px-3 py-2"
                ></textarea>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg shadow-md transition-all transform hover:scale-[1.01]"
              >
                {loading ? 'Submitting...' : 'Submit Daily Report'}
              </button>
            </form>
          </div>
        )}

        {/* Feedback Tab */}
        {activeTab === 'feedback' && feedback && (
          <div className="space-y-6 animate-fade-in">
            {/* Risk Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className={`p-6 rounded-xl border-l-4 shadow-sm ${
                feedback.risk_level === 'High' ? 'bg-red-50 border-red-500' :
                feedback.risk_level === 'Medium' ? 'bg-yellow-50 border-yellow-500' :
                'bg-green-50 border-green-500'
              }`}>
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-gray-700 font-medium">Local Risk Status</h3>
                  <Thermometer className={
                    feedback.risk_level === 'High' ? 'text-red-500' :
                    feedback.risk_level === 'Medium' ? 'text-yellow-500' :
                    'text-green-500'
                  } />
                </div>
                <div className="text-3xl font-bold text-gray-800 mb-1">{feedback.risk_level} Risk</div>
                <div className="text-sm text-gray-500">Based on recent signals in {facility.location?.lga}</div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-gray-700 font-medium">Risk Trend</h3>
                  {feedback.risk_trend === 'Rising' ? <TrendingUp className="text-red-500" /> :
                   feedback.risk_trend === 'Falling' ? <TrendingDown className="text-green-500" /> :
                   <Minus className="text-gray-400" />}
                </div>
                <div className="text-3xl font-bold text-gray-800 mb-1">{feedback.risk_trend}</div>
                <div className="text-sm text-gray-500">Compared to last week</div>
              </div>
            </div>

            {/* Warning Message */}
            <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg flex items-start">
              <AlertTriangle className="text-orange-500 mr-3 flex-shrink-0 mt-1" />
              <div>
                <h4 className="font-bold text-orange-800">System Warning</h4>
                <p className="text-orange-700">{feedback.warning_message}</p>
              </div>
            </div>

            {/* Comparison Chart */}
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-800 mb-6">Your Facility vs. LGA Average (Today)</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip cursor={{ fill: 'transparent' }} />
                    <Legend />
                    <Bar dataKey="my" name="My Facility" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="lga" name="LGA Average" fill="#9ca3af" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-center text-sm text-gray-500 mt-4">
                Comparison helps identify if your facility is an outlier or part of a wider trend.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
